from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import ResourseCharacterResponse
from ...services.location_resources_character import LocationResourcesCharacterServiceProtocol


class GetMyUseCaseProtocol(UseCaseProtocol[list[ResourseCharacterResponse]]):
    async def __call__(self, user: UserTokenDataReadSchema) -> list[ResourseCharacterResponse]:
        ...

class GetMyUseCase(GetMyUseCaseProtocol):
    def __init__(self, service: LocationResourcesCharacterServiceProtocol):
        self.service = service

    async def __call__(self, user: UserTokenDataReadSchema) -> list[ResourseCharacterResponse]:
        if not user.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_all_my(user.character_id)