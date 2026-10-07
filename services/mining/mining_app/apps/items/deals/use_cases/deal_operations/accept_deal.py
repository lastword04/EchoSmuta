import uuid
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import DealStatus
from ...exceptions import DealAccessDeniedError, DealNotFoundError, DealStateError
from ...repositories import DealRepositoryProtocol
from ...schemas import DealReadSchema
from ._base import DEAL_LIFETIME, _character_id, _DealUseCase, _publish_deal_event


class AcceptDealUseCaseProtocol(UseCaseProtocol[DealReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealReadSchema: ...


class AcceptDealUseCase(_DealUseCase, AcceptDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository = repository
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealReadSchema:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            deal = await self.repository.get_for_participant(deal_id, character_id, for_update=True)
            if not deal:
                raise DealNotFoundError(deal_id)
            if deal.partner_character_id != character_id:
                raise DealAccessDeniedError()
            if deal.status != DealStatus.DRAFT:
                raise DealStateError("Only a draft deal can be accepted")
            await self._ensure_proximity(deal.initiator_character_id, deal.partner_character_id, deal.location_slug)
            deal.status = DealStatus.ACTIVE
            deal.expires_at = datetime.now(UTC) + DEAL_LIFETIME
        await _publish_deal_event(self.deal_events, deal, DealEventType.ACCEPTED)
        return DealReadSchema.model_validate(deal)
