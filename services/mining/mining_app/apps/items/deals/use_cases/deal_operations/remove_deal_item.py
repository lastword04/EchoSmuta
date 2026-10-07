import uuid
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ....models import InventoryItem
from ...enums import (
    DealAssetType,
    ResourceReservationStatus,
)
from ...exceptions import DealAssetUnavailableError
from ...repositories import (
    DealItemRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
    DealResourceReservationRepositoryProtocol,
)
from ._base import _character_id, _DealUseCase, _publish_deal_event


class RemoveDealItemUseCaseProtocol(UseCaseProtocol[None], Protocol):
    async def __call__(self, deal_id: uuid.UUID, deal_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> None: ...
    async def remove_resource(self, deal_id: uuid.UUID, resource_slug: str, user: UserTokenDataReadSchema) -> None: ...


class RemoveDealItemUseCase(_DealUseCase, RemoveDealItemUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, reservation_repository: DealResourceReservationRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository, self.offer_repository, self.item_repository, self.reservation_repository = repository, offer_repository, item_repository, reservation_repository
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, deal_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> None:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            deal, offer = await self._prepare_offer(self.repository, self.offer_repository, deal_id, character_id)
            deal_item = await self.item_repository.get_for_deal_item(deal.id, deal_item_id, for_update=True)
            if not deal_item or deal_item.offer_id != offer.id:
                raise DealAssetUnavailableError("Deal item not found in your offer")
            if deal_item.asset_type == DealAssetType.RESOURCE:
                reservation = await self.reservation_repository.get_active_for_item(deal_item.id, for_update=True)
                if reservation:
                    reservation.status = ResourceReservationStatus.RELEASED
            else:
                inventory_item = await self.repository.session.get(InventoryItem, deal_item.inventory_item_id, with_for_update=True)
                if inventory_item:
                    inventory_item.deal_id = None
            await self.repository.session.delete(deal_item)
            self._touch_offer(deal, offer, await self.offer_repository.get_by_deal(deal.id, for_update=True))
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"action": "remove"})

    async def remove_resource(self, deal_id: uuid.UUID, resource_slug: str, user: UserTokenDataReadSchema) -> None:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            deal, offer = await self._prepare_offer(self.repository, self.offer_repository, deal_id, character_id)
            deal_item = await self.item_repository.get_for_offer_asset(offer.id, DealAssetType.RESOURCE, resource_slug, for_update=True)
            if not deal_item:
                raise DealAssetUnavailableError("Resource is not present in your offer")
            reservation = await self.reservation_repository.get_active_for_item(deal_item.id, for_update=True)
            if reservation:
                reservation.status = ResourceReservationStatus.RELEASED
            await self.repository.session.delete(deal_item)
            self._touch_offer(deal, offer, await self.offer_repository.get_by_deal(deal.id, for_update=True))
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"action": "remove_resource"})
