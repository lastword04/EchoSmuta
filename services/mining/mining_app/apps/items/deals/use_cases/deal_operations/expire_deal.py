import logging
from datetime import UTC, datetime

from shared.schemas.deal_events import DealEventType

from .....resources.events.publisher import RedisPublisherProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import (
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from ...models import DealLedgerOperation
from ...repositories import (
    DealItemRepositoryProtocol,
    DealLedgerOperationRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
    DealResourceReservationRepositoryProtocol,
)
from ._base import _operation_id, _publish_deal_event

logger = logging.getLogger(__name__)


class ExpireDealUseCase:
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, reservation_repository: DealResourceReservationRepositoryProtocol, ledger_repository: DealLedgerOperationRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol, redis_publisher: RedisPublisherProtocol | None = None) -> None:
        self.repository, self.offer_repository, self.item_repository = repository, offer_repository, item_repository
        self.reservation_repository, self.ledger_repository, self.character_client = reservation_repository, ledger_repository, character_client
        self.deal_events = deal_events
        self.redis_publisher = redis_publisher

    async def __call__(self, limit: int = 50) -> int:
        now = datetime.now(UTC)
        async with self.repository.session.begin():
            deals = await self.repository.list_expired_for_update(now, limit)
            for deal in deals:
                offers = await self.offer_repository.get_by_deal(deal.id, for_update=True)
                for offer in offers:
                    for currency, amount in ((DealCurrency.DUCATS, offer.ducats_escrowed), (DealCurrency.GOLD, offer.gold_escrowed)):
                        if amount:
                            operation_id = _operation_id(deal.id, f"{offer.character_id}:{currency.value}:expire-refund")
                            if currency == DealCurrency.DUCATS:
                                await self.character_client.credit_ducats(offer.character_id, amount, operation_id, "deal_ducats_escrow_expire_refund", "mining.deals", item_meta={"deal_id": str(deal.id)})
                            else:
                                await self.character_client.credit_gold(offer.character_id, amount, operation_id, "deal_gold_escrow_expire_refund", "mining.deals", item_meta={"deal_id": str(deal.id)})
                            self.repository.session.add(DealLedgerOperation(deal_id=deal.id, operation_id=operation_id, operation_kind=DealLedgerOperationKind.ESCROW_RELEASE, character_id=offer.character_id, currency=currency, amount=amount, status=DealLedgerOperationStatus.APPLIED))
                await self.reservation_repository.release_active_for_deal(deal.id)
                await self.item_repository.clear_inventory_deal_id(deal.id)
                deal.status = DealStatus.EXPIRED
        for deal in deals:
            await _publish_deal_event(self.deal_events, deal, DealEventType.EXPIRED)
            
            # Публикация события для фронта (WS)
            if self.redis_publisher:
                try:
                    payload = {
                        "event_type": "economy_state_updated",
                        "data": {
                            "action": "deal_expired",
                            "initiator_character_id": str(deal.initiator_character_id),
                            "partner_character_id": str(deal.partner_character_id),
                            "location_slug": deal.location_slug,
                            "deal_id": str(deal.id),
                        }
                    }
                    await self.redis_publisher.publish("economy_state_updated", payload)
                except Exception as e:
                    logger.error(f"Failed to publish deal_expired economy state update: {e}")
        return len(deals)
