import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

import sqlalchemy as sa

from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....events.deals import DealEventsProtocol
from ....models import InventoryItem
from ...enums import (
    DealAssetType,
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)
from ...exceptions import (
    DealAccessDeniedError,
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
)
from ...schemas import DealReadSchema
from ._base import DEAL_LIFETIME, _operation_id, _publish_deal_event

logger = logging.getLogger(__name__)

class CancelDealUseCaseProtocol(UseCaseProtocol[DealReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, character_id: uuid.UUID) -> DealReadSchema: ...


class CancelDealUseCase(CancelDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol,
                 item_repository: DealItemRepositoryProtocol, reservation_repository: DealResourceReservationRepositoryProtocol,
                 ledger_repository: DealLedgerOperationRepositoryProtocol, deal_events: DealEventsProtocol,
                 character_client) -> None:
        self.repository = repository
        self.offer_repository = offer_repository
        self.item_repository = item_repository
        self.reservation_repository = reservation_repository
        self.ledger_repository = ledger_repository
        self.deal_events = deal_events
        self.character_client = character_client

    async def __call__(self, deal_id: uuid.UUID, character_id: uuid.UUID) -> DealReadSchema:
        async with self.repository.session.begin():
            deal = await self.repository.get_for_update(deal_id)
            if not deal:
                raise DealNotFoundError(deal_id)
            
            # Защита: нельзя отменять завершенные/истекшие сделки
            if deal.status in (DealStatus.COMPLETED, DealStatus.CANCELLED, DealStatus.EXPIRED):
                raise DealStateError("Deal is already in a final state")
            
            my_offer = await self.offer_repository.get_for_character(deal.id, character_id, for_update=True)
            if not my_offer:
                raise DealAccessDeniedError()

            # 1) Возврат денег ТОЛЬКО отменяющему — фиксируем НАМЕРЕНИЕ возврата
            # (строка в ledger со статусом PENDING). Сами HTTP-зачисления делаем
            # ПОСЛЕ коммита транзакции, чтобы не держать FOR UPDATE-локи на
            # deal/offers/items во время внешних вызовов (см. CompleteDealUseCase:
            # "Между транзакциями — ТОЛЬКО HTTP-запросы"). Именно удержание локов
            # во время HTTP делало отмену медленной и приводило к конкуренции
            # с параллельным редактированием оффера партнёром.
            refund_plans: list[tuple[DealCurrency, Decimal, uuid.UUID]] = []
            for currency, amount in ((DealCurrency.DUCATS, my_offer.ducats_escrowed), (DealCurrency.GOLD, my_offer.gold_escrowed)):
                op_id = _operation_id(deal.id, f"{character_id}:{currency.value}:cancel-refund:{my_offer.revision}")
                existing_op = await self.ledger_repository.get_by_operation_id(op_id)
                if existing_op is not None:
                    # APPLIED — возврат уже проведён ранее (повторная отмена)
                    if existing_op.status == DealLedgerOperationStatus.APPLIED:
                        continue
                    # PENDING — прошлый возврат не дошёл до characters-сервиса:
                    # повторяем HTTP (идемпотентно по operation_id)
                    refund_plans.append((currency, existing_op.amount, op_id))
                    continue
                if amount <= 0:
                    continue
                await self.ledger_repository.create_many([DealLedgerOperation(
                    deal_id=deal.id,
                    operation_id=op_id,
                    operation_kind=DealLedgerOperationKind.ESCROW_RELEASE,
                    character_id=character_id,
                    currency=currency,
                    amount=amount,
                    status=DealLedgerOperationStatus.PENDING,
                    payload={"operation_type": f"deal_{currency.value.lower()}_escrow_cancel_refund", "source": "mining.deals"},
                )])
                refund_plans.append((currency, amount, op_id))

            # 2) Освобождаем ТОЛЬКО мои предметы
            all_items = await self.item_repository.get_by_deal(deal.id, for_update=True)
            my_items = [it for it in all_items if it.offer_id == my_offer.id]
            for item in my_items:
                if item.asset_type == DealAssetType.RESOURCE:
                    reservation = await self.reservation_repository.get_active_for_item(item.id, for_update=True)
                    if reservation:
                        reservation.status = ResourceReservationStatus.RELEASED
                else:
                    inventory_item = await self.repository.session.get(InventoryItem, item.inventory_item_id, with_for_update=True)
                    if inventory_item:
                        inventory_item.deal_id = None
                await self.repository.session.delete(item)

            # 3) Обнуляем мой оффер и сбрасываем подтверждения
            my_offer.ducats_amount = Decimal(0)
            my_offer.ducats_escrowed = Decimal(0)
            my_offer.gold_amount = Decimal(0)
            my_offer.gold_escrowed = Decimal(0)
            my_offer.confirmed_revision = None
            my_offer.revision += 1
            
            for other in await self.offer_repository.get_by_deal(deal.id, for_update=True):
                other.confirmed_revision = None

            if character_id == deal.initiator_character_id:
                deal.initiator_confirmed_at = None
            else:
                deal.partner_confirmed_at = None

            # 4) СДЕЛКА ВСЕГДА ОСТАЁТСЯ ЖИВОЙ! Статус НЕ МЕНЯЕМ.
            deal.cancelled_by_character_id = character_id
            deal.expires_at = datetime.now(UTC) + DEAL_LIFETIME

        # ── Между транзакциями — ТОЛЬКО HTTP-зачисления, никаких SQL-локов ──
        # Идемпотентность обеспечивает operation_id (characters-сервис не
        # зачисляет дважды). Если вызов упал — строка остаётся в PENDING и
        # возврат доводится повторной отменой (сделка остаётся живой).
        for refund_currency, refund_amount, refund_op_id in refund_plans:
            if refund_currency == DealCurrency.DUCATS:
                await self.character_client.credit_ducats(
                    character_id, refund_amount, refund_op_id,
                    "deal_ducats_escrow_cancel_refund", "mining.deals",
                    item_meta={"deal_id": str(deal.id)},
                )
            else:
                await self.character_client.credit_gold(
                    character_id, refund_amount, refund_op_id,
                    "deal_gold_escrow_cancel_refund", "mining.deals",
                    item_meta={"deal_id": str(deal.id)},
                )

        # ── Финальная транзакция: помечаем возвраты проведёнными ──
        if refund_plans:
            async with self.repository.session.begin():
                await self.repository.session.execute(
                    sa.update(DealLedgerOperation)
                    .where(DealLedgerOperation.operation_id.in_([op_id for _, _, op_id in refund_plans]))
                    .values(status=DealLedgerOperationStatus.APPLIED)
                )

        # ВСЕГДА отправляем UPDATED, чтобы партнер увидел изменения
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"action": "cancel_side"})
        return DealReadSchema.model_validate(deal)

class CancelDealsForCharacterUseCase:
    """Автоматически отменяет все активные сделки персонажа (при оффлайне или смене локации)."""
    
    def __init__(
        self, 
        repository: DealRepositoryProtocol, 
        cancel_use_case: CancelDealUseCaseProtocol
    ) -> None:
        self.repository = repository
        self.cancel_use_case = cancel_use_case

    async def __call__(self, character_id: uuid.UUID) -> int:
        deals = await self.repository.list_active_for_character(character_id)
        cancelled_count = 0
        
        for deal in deals:
            try:
                # ✅ ТЕПЕРЬ МЫ ПРОСТО ПЕРЕДАЕМ character_id. Никаких фейковых юзеров!
                await self.cancel_use_case(deal.id, character_id)
                cancelled_count += 1
            except DealStateError:
                # Сделка уже завершена или отменена, игнорируем
                continue
            except Exception as e:
                logger.warning(f"Failed to auto-cancel deal {deal.id} for character {character_id}: {e}")
        
        return cancelled_count
    
