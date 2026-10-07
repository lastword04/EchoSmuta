from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import DealStatus
from ...exceptions import DealSelfPartnerError
from ...models import Deal, DealOffer
from ...repositories import DealOfferRepositoryProtocol, DealRepositoryProtocol
from ...schemas import DealCreateSchema, DealReadSchema
from ._base import DEAL_LIFETIME, _character_id, _DealUseCase, _publish_deal_event


class CreateDealUseCaseProtocol(UseCaseProtocol[DealReadSchema], Protocol):
    async def __call__(self, user: UserTokenDataReadSchema, data: DealCreateSchema) -> DealReadSchema: ...


class CreateDealUseCase(_DealUseCase, CreateDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository = repository
        self.offer_repository = offer_repository
        self.deal_events = deal_events

    async def __call__(self, user: UserTokenDataReadSchema, data: DealCreateSchema) -> DealReadSchema:
        initiator_id = _character_id(user)
        if initiator_id == data.partner_character_id:
            raise DealSelfPartnerError()
        await self._ensure_proximity(initiator_id, data.partner_character_id, data.location_slug)
        now = datetime.now(UTC)
        async with self.repository.session.begin():
            deal = Deal(initiator_character_id=initiator_id, partner_character_id=data.partner_character_id, location_slug=data.location_slug, status=DealStatus.DRAFT, expires_at=now + DEAL_LIFETIME)
            self.repository.session.add(deal)
            await self.repository.session.flush()
            self.repository.session.add_all([DealOffer(deal_id=deal.id, character_id=initiator_id), DealOffer(deal_id=deal.id, character_id=data.partner_character_id)])
        await _publish_deal_event(self.deal_events, deal, DealEventType.CREATED)
        return DealReadSchema.model_validate(deal)
