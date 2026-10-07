import uuid
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema

from ......core.use_cases import UseCaseProtocol
from ...enums import DealStatus
from ...exceptions import DealNotFoundError
from ...repositories import (
    DealItemRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
)
from ...schemas import (
    CompletingDealListSchema,
    DealDetailSchema,
    DealListSchema,
    DealOfferReadSchema,
    DealReadSchema,
    NearbyPartnerSchema,
)
from ._base import _character_id, _DealUseCase
from .complete_deal import CompleteDealUseCaseProtocol


class ListDealsUseCaseProtocol(UseCaseProtocol[DealListSchema], Protocol):
    async def __call__(self, user: UserTokenDataReadSchema, statuses: list[DealStatus] | None, limit: int, offset: int) -> DealListSchema: ...


class ListDealsUseCase(ListDealsUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self, user: UserTokenDataReadSchema, statuses: list[DealStatus] | None, limit: int, offset: int) -> DealListSchema:
        deals, count = await self.repository.list_for_participant(_character_id(user), statuses, limit, offset)
        return DealListSchema(objects=[DealReadSchema.model_validate(deal) for deal in deals], count=count)


class GetDealUseCaseProtocol(UseCaseProtocol[DealDetailSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealDetailSchema: ...


class GetDealUseCase(GetDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol) -> None:
        self.repository = repository
        self.offer_repository = offer_repository
        self.item_repository = item_repository

    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealDetailSchema:
        detail = await self.repository.get_detail_for_participant(deal_id, _character_id(user))
        if not detail:
            raise DealNotFoundError(deal_id)
        deal, offers, items = detail
        return DealDetailSchema(**DealReadSchema.model_validate(deal).model_dump(), offers=[DealOfferReadSchema.model_validate(offer) for offer in offers], items=items)


class ListNearbyPartnersUseCaseProtocol(UseCaseProtocol[list[NearbyPartnerSchema]], Protocol):
    async def __call__(self, user: UserTokenDataReadSchema, location_slug: str) -> list[NearbyPartnerSchema]: ...


class ListNearbyPartnersUseCase(_DealUseCase, ListNearbyPartnersUseCaseProtocol):
    async def __call__(self, user: UserTokenDataReadSchema, location_slug: str) -> list[NearbyPartnerSchema]:
        character_id = _character_id(user)
        online = await self._online_at_location(location_slug)
        return [NearbyPartnerSchema(id=character.id, name=character.name, level=character.level, location_slug=character.location_slug) for character in online.objects if character.id != character_id]


class RecoverCompletingDealsUseCase:
    def __init__(self, repository: DealRepositoryProtocol, complete_use_case: CompleteDealUseCaseProtocol) -> None:
        self.repository = repository
        self.complete_use_case = complete_use_case

    async def __call__(self, limit: int = 50) -> int:
        deals = await self.repository.list_completing(limit)
        completed = 0
        for deal in deals:
            await self.complete_use_case(deal.id)
            completed += 1
        return completed


class ListCompletingDealsUseCase:
    def __init__(self, repository: DealRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self, limit: int) -> CompletingDealListSchema:
        deals = await self.repository.list_completing(limit)
        return CompletingDealListSchema(objects=[DealReadSchema.model_validate(deal) for deal in deals], count=len(deals))
