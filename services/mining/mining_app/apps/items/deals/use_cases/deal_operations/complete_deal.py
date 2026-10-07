import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from .....resources.events.publisher import RedisPublisherProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import (
    DealAssetType,
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from ...exceptions import (
    DealCompletionError,
    DealGoldTradeDisabledError,
    DealNotFoundError,
    DealStateError,
)
from ...models import DealLedgerOperation
from ...repositories import (
    DealItemRepositoryProtocol,
    DealLedgerOperationRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
    DealResourceReservationRepositoryProtocol,
    TradeLicenseRepositoryProtocol,
)
from ...schemas import DealReadSchema
from ._base import (
    _DealUseCase,
    _goods_prices,
    _operation_id,
    _publish_deal_event,
    _validate_deal_economy,
)

logger = logging.getLogger(__name__)

class CompleteDealUseCaseProtocol(UseCaseProtocol[DealReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID) -> DealReadSchema: ...


class CompleteDealUseCase(_DealUseCase, CompleteDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, reservation_repository: DealResourceReservationRepositoryProtocol, ledger_repository: DealLedgerOperationRepositoryProtocol, license_repository: TradeLicenseRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_tax: float, discounted_tax: float, deal_events: DealEventsProtocol, redis_publisher: RedisPublisherProtocol | None = None) -> None:
        super().__init__(character_client)
        self.repository, self.offer_repository, self.item_repository = repository, offer_repository, item_repository
        self.reservation_repository, self.ledger_repository, self.license_repository = reservation_repository, ledger_repository, license_repository
        self.deal_tax, self.discounted_tax = Decimal(str(deal_tax)), Decimal(str(discounted_tax))
        self.deal_events = deal_events
        self.redis_publisher = redis_publisher

    async def __call__(self, deal_id: uuid.UUID) -> DealReadSchema:
        payouts: list[tuple[uuid.UUID, DealCurrency, Decimal, uuid.UUID]] = []
        assets_transferred = False
        tax_rates: dict[uuid.UUID, Decimal] = {}
        incoming_weights: dict[uuid.UUID, int] = {}
        async with self.repository.session.begin():
            deal = await self.repository.get_for_update(deal_id)
            if not deal:
                raise DealNotFoundError(deal_id)
            offers = await self.offer_repository.get_by_deal(deal.id, for_update=True)
            items = await self.item_repository.get_by_deal(deal.id, for_update=True)
            if deal.status == DealStatus.COMPLETED:
                return DealReadSchema.model_validate(deal)
            if deal.status not in (DealStatus.ACTIVE, DealStatus.COMPLETING) or len(offers) != 2 or any(offer.confirmed_revision != offer.revision for offer in offers):
                raise DealStateError("Deal is not ready for completion")
            await self._ensure_proximity(deal.initiator_character_id, deal.partner_character_id, deal.location_slug)
            for offer in offers:
                if offer.ducats_amount != offer.ducats_escrowed or offer.gold_amount != offer.gold_escrowed:
                    raise DealCompletionError("Escrow does not match the current offer")
                if offer.gold_amount and not (await self.character_client.get_trade_privileges(offer.character_id)).gold_trade_enabled:
                    raise DealGoldTradeDisabledError()
            
            # 🛡️ Предзагружаем ВСЁ внутри первой транзакции
            for recipient_id in (deal.initiator_character_id, deal.partner_character_id):
                balance = await self.character_client.get_character_weight_balance(recipient_id)
                incoming = await self.item_repository.incoming_weight(deal.id, recipient_id)
                incoming_weights[recipient_id] = incoming
                if balance.weight + incoming > balance.max_weight:
                    raise DealCompletionError("Одна из сторон сделки не может принять предметы из-за превышения лимита веса")
                license_ = await self.license_repository.get_for_character(recipient_id)
                tax_rates[recipient_id] = self.discounted_tax if license_ and license_.end_date > datetime.now(UTC) else self.deal_tax
            # 🎭 Роли сделки и цена (финальная проверка)
            item_prices, resource_prices = await _goods_prices(self.repository.session, items)
            _validate_deal_economy(deal, offers, items, item_prices, resource_prices)
            # 🛡️ Защита (escrow): передаваемые предметы не должны быть надеты —
            # иначе transfer_assets сменит character_id, а запись в
            # character_equipment останется у отправителя. Экипировать предмет
            # в сделке нельзя (EquipItemUseCase) — здесь ловим гонки и legacy-данные.
            for it in items:
                if it.asset_type != DealAssetType.INVENTORY_ITEM:
                    continue
                trade_row = await self.item_repository.get_inventory_for_trade(it.inventory_item_id, for_update=True)
                if trade_row is not None:
                    _inv_item, _item, equipped, _for_sale = trade_row
                    if equipped:
                        item_name = (it.item_snapshot or {}).get("name", "Предмет")
                        raise DealCompletionError(
                            f"Предмет «{item_name}» надет — снимите его перед подтверждением сделки"
                        )
            deal.status = DealStatus.COMPLETING
        
        # Между транзакциями — ТОЛЬКО HTTP-запросы, никаких SQL!
        try:
            for offer in offers:
                recipient_id = deal.partner_character_id if offer.character_id == deal.initiator_character_id else deal.initiator_character_id
                tax_rate = tax_rates[recipient_id]
                ducats_tax = (offer.ducats_escrowed * tax_rate).quantize(Decimal("0.01"))
                gold_tax = (offer.gold_escrowed * tax_rate).quantize(Decimal("0.01"))
                for currency, amount, tax_amount in ((DealCurrency.DUCATS, offer.ducats_escrowed, ducats_tax), (DealCurrency.GOLD, offer.gold_escrowed, gold_tax)):
                    if not amount:
                        continue
                    income = amount - tax_amount
                    if income:
                        operation_id = _operation_id(deal.id, f"{recipient_id}:{currency.value}:income")
                        if currency == DealCurrency.DUCATS:
                            await self.character_client.credit_ducats(recipient_id, income, operation_id, "deal_ducats_transfer_income", "mining.deals", counterparty_id=offer.character_id, item_meta={"deal_id": str(deal.id)})
                        else:
                            await self.character_client.credit_gold(recipient_id, income, operation_id, "deal_gold_transfer_income", "mining.deals", {"deal_id": str(deal.id), "offer_character_id": str(offer.character_id)})
                        payouts.append((recipient_id, currency, income, operation_id))
            
            async with self.repository.session.begin():
                deal = await self.repository.get_for_update(deal_id)
                if not deal or deal.status != DealStatus.COMPLETING:
                    raise DealStateError("Deal completion was interrupted")
                offers = await self.offer_repository.get_by_deal(deal.id, for_update=True)
                items = await self.item_repository.get_by_deal(deal.id, for_update=True)
                await self.item_repository.transfer_assets(deal, items)
                assets_transferred = True
                await self.reservation_repository.mark_transferred_for_deal(deal.id)
                operations = []
                for offer in offers:
                    recipient_id = deal.partner_character_id if offer.character_id == deal.initiator_character_id else deal.initiator_character_id
                    tax_rate = tax_rates[recipient_id]
                    for currency, amount in ((DealCurrency.DUCATS, offer.ducats_escrowed), (DealCurrency.GOLD, offer.gold_escrowed)):
                        if amount:
                            operations.append(DealLedgerOperation(deal_id=deal.id, operation_id=_operation_id(deal.id, f"{recipient_id}:{currency.value}:income"), operation_kind=DealLedgerOperationKind.TRANSFER, character_id=recipient_id, counterparty_id=offer.character_id, currency=currency, amount=amount, status=DealLedgerOperationStatus.APPLIED))
                            tax_amount = (amount * tax_rate).quantize(Decimal("0.01"))
                            if tax_amount:
                                operations.append(DealLedgerOperation(deal_id=deal.id, operation_id=_operation_id(deal.id, f"{recipient_id}:{currency.value}:tax"), operation_kind=DealLedgerOperationKind.TAX, character_id=recipient_id, counterparty_id=offer.character_id, currency=currency, amount=tax_amount, status=DealLedgerOperationStatus.APPLIED, payload={"operation_type": f"deal_{currency.value.lower()}_trade_tax"}))
                await self.ledger_repository.create_many(operations)
                deal.status, deal.completed_at = DealStatus.COMPLETED, datetime.now(UTC)

            # === Формируем АГРЕГИРОВАННЫЕ системные сообщения ===
            system_messages = []
            deal_short_id = deal.id.hex[:8].upper()

            for offer in offers:
                recipient_id = deal.partner_character_id if offer.character_id == deal.initiator_character_id else deal.initiator_character_id
                sender_id = offer.character_id

                sender_info = await self.character_client.get_simple_info_character(sender_id)
                sender_name = sender_info.name if sender_info else "Неизвестный"

                rewards_parts = []
                total_tax = Decimal(0)
                total_gold_tax = Decimal(0)
                tax_rate = tax_rates[recipient_id]

                # Дукаты
                if offer.ducats_escrowed > 0:
                    rewards_parts.append(f"{offer.ducats_escrowed} дт")
                    total_tax += (offer.ducats_escrowed * tax_rate).quantize(Decimal("0.01"))

                # Золото
                if offer.gold_escrowed > 0:
                    rewards_parts.append(f"{offer.gold_escrowed} злт")
                    total_gold_tax += (offer.gold_escrowed * tax_rate).quantize(Decimal("0.01"))

                # Предметы и ресурсы от этого отправителя
                for item in items:
                    if item.owner_character_id == sender_id:
                        if item.asset_type == DealAssetType.INVENTORY_ITEM:
                            item_name = item.item_snapshot.get("name", "Предмет")
                            rewards_parts.append(f"{item_name} {item.amount} шт" if item.amount > 1 else item_name)
                        elif item.asset_type == DealAssetType.RESOURCE:
                            resource_name = item.item_snapshot.get("name", "Ресурс")
                            rewards_parts.append(f"{resource_name} {item.amount} шт")

                if rewards_parts:
                    rewards_list = ", ".join(rewards_parts)
                    tax_parts = []
                    if total_tax > 0:
                        tax_parts.append(f"{total_tax} дт")
                    if total_gold_tax > 0:
                        tax_parts.append(f"{total_gold_tax} злт")
                    tax_str = " + ".join(tax_parts)
                    template_key = "items.locations.trade_hall.deal.completed_with_tax" if tax_str else "items.locations.trade_hall.deal.completed_without_tax"

                    system_messages.append({
                        "character_id": str(recipient_id),
                        "template_key": template_key,
                        "params": {
                            "deal_short_id": deal_short_id,
                            "partner_name": sender_name,
                            "rewards_list": rewards_list,
                            "tax": tax_str
                        }
                    })

            await _publish_deal_event(self.deal_events, deal, DealEventType.COMPLETED, details={"system_messages": system_messages})
            
            # Публикация события для фронта (WS)
            if self.redis_publisher:
                try:
                    payload = {
                        "event_type": "economy_state_updated",
                        "data": {
                            "action": "deal_completed",
                            "initiator_character_id": str(deal.initiator_character_id),
                            "partner_character_id": str(deal.partner_character_id),
                            "location_slug": deal.location_slug,
                            "deal_id": str(deal.id),
                        }
                    }
                    await self.redis_publisher.publish("economy_state_updated", payload)
                except Exception as e:
                    logger.error(f"Failed to publish deal_completed economy state update: {e}")
            
            return DealReadSchema.model_validate(deal)

        except Exception:
            if not assets_transferred:
                for character_id, currency, amount, payout_operation_id in reversed(payouts):
                    compensation_id = _operation_id(deal_id, f"{payout_operation_id}:compensation")
                    operation_type = f"deal_{currency.value.lower()}_transfer_income_compensation"
                    try:
                        if currency == DealCurrency.DUCATS:
                            await self.character_client.debit_ducats(character_id, amount, compensation_id, operation_type, "mining.deals", item_meta={"deal_id": str(deal_id), "compensates": str(payout_operation_id)})
                        else:
                            await self.character_client.debit_gold(character_id, amount, compensation_id, operation_type, "mining.deals", item_meta={"deal_id": str(deal_id), "compensates": str(payout_operation_id)})
                    except Exception:
                        logger.exception("Failed to compensate after deal error")
            raise


