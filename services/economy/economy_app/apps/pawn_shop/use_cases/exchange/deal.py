import uuid
from decimal import Decimal
from typing import Any
import logging

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...models import EconomyTransaction, ExchangeLot, LotStatus, LotType, Resource, TransactionType
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from shared.utils.plural import plural
from .utils import raise_external_error, split_bundle_price

logger = logging.getLogger(__name__)


class DealExchangeLotUseCase:
    def __init__(self, characters_client: CharactersClient, mining_client: MiningClient,
                 economy_events: EconomyEventsProtocol, template_service: EconomyTemplateServiceProtocol) -> None:
        self.characters_client = characters_client
        self.mining_client = mining_client
        self.economy_events = economy_events
        self.template_service = template_service

    async def __call__(self, lot_id: uuid.UUID, character_id: uuid.UUID, session: AsyncSession) -> dict[str, Any]:
        lot = await session.scalar(select(ExchangeLot).where(ExchangeLot.id == lot_id).with_for_update())
        if lot is None:
            raise HTTPException(status_code=404, detail="Лот не найден")
        if lot.status != LotStatus.ACTIVE:
            raise HTTPException(status_code=409, detail="Лот неактивен")
        if lot.owner_character_id == character_id:
            raise HTTPException(status_code=400, detail="Нельзя купить собственный лот")

        items = list(lot.items)
        resources = (await session.scalars(
            select(Resource).where(Resource.id.in_([i.resource_id for i in items]))
        )).all()
        resource_map = {r.id: r for r in resources}

        amount = lot.price
        operation_id = uuid.uuid4()

        if lot.lot_type == LotType.SELL:
            buyer_id = character_id
            seller_id = lot.owner_character_id
        else:
            seller_id = character_id
            buyer_id = lot.owner_character_id

        # === ПРОВЕРКА МИНИМАЛЬНОЙ ЦЕНЫ ЛОТА (для старых лотов) ===
        MIN_LOT_VALUE_RATIO = Decimal("0.5")
        bundle_value = sum(
            Decimal(str(item.quantity)) * Decimal(str(resource_map[item.resource_id].base_sell_price))
            for item in items
        )
        bundle_value_half = (bundle_value * MIN_LOT_VALUE_RATIO).quantize(Decimal("0.01"))
        if Decimal(str(lot.price)) < bundle_value_half:
            raise HTTPException(
                status_code=409,
                detail="Лот создан по устаревшим правилам. Попросите владельца пересоздать лот."
            )
        # === КОНЕЦ ПРОВЕРКИ ===

        # === БЛОК ВАЛИДАЦИИ ДО ТРАНЗАКЦИЙ ===
        if lot.lot_type == LotType.SELL:
            # Исполнитель покупает — нужны дукаты на всю цену
            executor_balance = await self.characters_client.get_balance(character_id)
            if executor_balance < amount:
                raise HTTPException(status_code=409, detail="Недостаточно дукатов.")
        else:
            # Исполнитель продаёт — нужны ВСЕ ресурсы бандла
            try:
                payload = await self.mining_client.get_player_resources(character_id)
                resources_payload = payload.get("resources", payload if isinstance(payload, list) else [])
                amounts = {r.get("resource_slug"): int(r.get("amount", 0)) for r in resources_payload}
                for item in items:
                    resource = resource_map[item.resource_id]
                    if amounts.get(resource.code, 0) < item.quantity:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Недостаточно ресурса {resource.name} для сделки."
                        )
            except httpx.HTTPError:
                raise HTTPException(status_code=502, detail="Mining service is unavailable")
        # === КОНЕЦ БЛОКА ВАЛИДАЦИИ ===

        currency_operation_root_id = uuid.uuid5(
            lot.id,
            f"exchange-deal:{seller_id}:{buyer_id}:{amount}",
        )

        try:
            trade_license = await self.mining_client.get_trade_license(seller_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail="Mining service is unavailable") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Mining service is unavailable") from exc

        tax_rate = Decimal(str(trade_license["exchange_tax_rate"]))
        tax = (amount * tax_rate).quantize(Decimal("0.01"))
        net = amount - tax
        item_meta = {
            "lot_id": str(lot.id),
            "gross": str(amount),
            "tax": str(tax),
            "net": str(net),
        }

        paid = False
        moved: list[tuple[str, int, str]] = []  # (код ресурса, кол-во, стадия: debited/credited)

        async def compensate():
            """Сага: откат внешних эффектов при сбое."""
            nonlocal paid, moved
            if paid:
                try:
                    await self.characters_client.credit(
                        buyer_id, amount,
                        operation_id=uuid.uuid5(currency_operation_root_id, "payment-compensation"),
                        operation_type="exchange_deal_payment_compensation",
                        source="economy.exchange",
                        counterparty_id=seller_id,
                        item_meta={"lot_id": str(lot.id)},
                    )
                except Exception as ce:
                    logger.error("Exchange payment compensation failed for lot %s: %s", lot.id, ce)
            for code, qty, stage in moved:
                try:
                    if stage == "credited":
                        await self.mining_client.debit(
                            code, buyer_id, qty,
                            uuid.uuid5(currency_operation_root_id, f"comp-debit-{code}"),
                        )
                    await self.mining_client.credit(
                        code, seller_id, qty,
                        uuid.uuid5(currency_operation_root_id, f"comp-credit-{code}"),
                    )
                except Exception as ce:
                    logger.error("Exchange resource compensation failed for lot %s: %s", lot.id, ce)
            paid = False
            moved = []

        try:
            if lot.lot_type == LotType.SELL:
                # Покупатель платит и получает ВСЕ ресурсы
                await self.characters_client.debit(
                    buyer_id,
                    amount,
                    operation_id=uuid.uuid5(currency_operation_root_id, "payment"),
                    operation_type="exchange_deal_payment",
                    source="economy.exchange",
                    counterparty_id=seller_id,
                    item_meta={"lot_id": str(lot.id)},
                )
                paid = True
                for item in items:
                    resource = resource_map[item.resource_id]
                    await self.mining_client.credit(
                        resource.code, buyer_id, item.quantity,
                        uuid.uuid5(currency_operation_root_id, f"credit-{resource.code}"),
                    )
                    moved.append((resource.code, item.quantity, "credited"))
            else:
                # Исполнитель передаёт ВСЕ ресурсы владельцу лота
                for item in items:
                    resource = resource_map[item.resource_id]
                    await self.mining_client.debit(
                        resource.code, seller_id, item.quantity,
                        uuid.uuid5(currency_operation_root_id, f"debit-{resource.code}"),
                    )
                    moved.append((resource.code, item.quantity, "debited"))
                    await self.mining_client.credit(
                        resource.code, buyer_id, item.quantity,
                        uuid.uuid5(currency_operation_root_id, f"credit-{resource.code}"),
                    )
                    moved[-1] = (resource.code, item.quantity, "credited")
            await self.characters_client.credit(
                seller_id,
                amount,
                operation_id=uuid.uuid5(currency_operation_root_id, "income"),
                operation_type="exchange_deal_income",
                source="economy.exchange",
                counterparty_id=buyer_id,
                item_meta=item_meta,
            )
            await self.characters_client.debit(
                seller_id,
                tax,
                operation_id=uuid.uuid5(currency_operation_root_id, "tax"),
                operation_type="exchange_deal_tax",
                source="economy.exchange",
                counterparty_id=buyer_id,
                item_meta=item_meta,
            )
        except httpx.HTTPStatusError as exc:
            await compensate()
            raise_external_error(exc, "External service rejected exchange deal")
        except httpx.HTTPError as exc:
            await compensate()
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        lot.status = LotStatus.FILLED

        # Транзакции по каждой позиции (цена распределена пропорционально)
        shares = split_bundle_price(amount, items, resource_map)
        for item in items:
            share = shares[item.resource_id]
            price_per_unit = (share / item.quantity).quantize(Decimal("0.01"))
            session.add(EconomyTransaction(
                transaction_type=TransactionType.EXCHANGE_BUY,
                resource_id=item.resource_id,
                quantity=item.quantity,
                price_per_unit=price_per_unit,
                total=share,
                buyer_id=buyer_id,
                seller_id=seller_id,
                lot_id=lot.id,
            ))
            session.add(EconomyTransaction(
                transaction_type=TransactionType.EXCHANGE_SELL,
                resource_id=item.resource_id,
                quantity=item.quantity,
                price_per_unit=price_per_unit,
                total=share,
                buyer_id=buyer_id,
                seller_id=seller_id,
                lot_id=lot.id,
            ))
        await session.commit()

        # ═══ Получаем локации и имена участников (один раз для всего блока) ═══
        try:
            executor_location = await self.characters_client.get_character_location(character_id)
        except Exception as e:
            logger.warning(f"Failed to get executor location: {e}")
            executor_location = "unknown"

        try:
            owner_location = await self.characters_client.get_character_location(lot.owner_character_id)
        except Exception as e:
            logger.warning(f"Failed to get owner location: {e}")
            owner_location = "unknown"

        try:
            executor_name = await self.characters_client.get_character_name(character_id)
        except Exception as e:
            logger.warning(f"Failed to get executor name: {e}")
            executor_name = "Неизвестный игрок"

        # ═══ Публикуем событие биржи (широковещательно в локацию) ═══
        try:
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "lot_sold",
                    "lot_id": str(lot.id),
                    "location_slug": executor_location,
                    "initiator_character_id": str(buyer_id),
                    "partner_character_id": str(seller_id),
                },
            )
            logger.info(f"✅ Published lot_sold event for lot {lot.id} to location {executor_location}")
        except Exception as e:
            logger.error(f"Failed to publish lot_sold event: {e}")

        # Формируем текст ресурсов из всех позиций
        items_parts = []
        for item in items:
            resource = resource_map[item.resource_id]
            items_parts.append(
                f"{item.quantity} {plural(item.quantity, 'брикет', 'брикета', 'брикетов')} ресурса {resource.name}"
            )
        items_text = ", ".join(items_parts)

        # Публикуем сообщения
        try:
            if lot.lot_type == LotType.SELL:
                executor_message = self.template_service.get_exchange_deal_buy_executor_message(
                    items=items_text,
                    price=str(amount),
                )
                executor_event_type = "economy_exchange_deal_buy_executor"
            else:
                executor_message = self.template_service.get_exchange_deal_sell_executor_message(
                    items=items_text,
                    price=str(net),
                    tax=str(tax),
                )
                executor_event_type = "economy_exchange_deal_sell_executor"

            await self.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type=executor_event_type,
                    character_id=character_id,
                    location_slug=executor_location,
                    content=executor_message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                )
            )

            if lot.lot_type == LotType.SELL:
                owner_message = self.template_service.get_exchange_deal_sell_owner_message(
                    items=items_text,
                    price=str(net),
                    executor_name=executor_name,
                    tax=str(tax),
                )
                owner_event_type = "economy_exchange_deal_sell_owner"
            else:
                owner_message = self.template_service.get_exchange_deal_buy_owner_message(
                    items=items_text,
                    price=str(amount),
                    executor_name=executor_name,
                )
                owner_event_type = "economy_exchange_deal_buy_owner"

            await self.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type=owner_event_type,
                    character_id=lot.owner_character_id,
                    location_slug=owner_location,
                    content=owner_message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[lot.owner_character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish exchange deal events: {e}")

        return {"lot_id": lot.id, "total_price": amount, "operation_id": operation_id, "status": lot.status}