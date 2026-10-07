from shared.schemas.auth import UserTokenDataReadSchema

from ....core.use_cases import UseCaseProtocol
from ....core.utils.exceptions import PermissionDeniedError
from ..schemas import LocationResourcesAndCharacterStats
from ..services.location_resources_character import LocationResourcesCharacterServiceProtocol


class GetResourcesForCharacterUseCaseProtocol(UseCaseProtocol[LocationResourcesAndCharacterStats]):
    async def __call__(self, user: UserTokenDataReadSchema, location_slug: str | None = None) -> LocationResourcesAndCharacterStats:
        ...


class GetResourcesForCharacterUseCase(GetResourcesForCharacterUseCaseProtocol):
    def __init__(self, service: LocationResourcesCharacterServiceProtocol):
        self.service = service

    async def __call__(self, user: UserTokenDataReadSchema, location_slug: str | None = None) -> LocationResourcesAndCharacterStats:
        if not user.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_resources_with_amount_by_character(
            user.character_id,
            location_slug=location_slug
        )