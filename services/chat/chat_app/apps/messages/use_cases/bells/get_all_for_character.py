from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.bells import FavoriteBellsServiceProtocol
from ...schemas import FavoriteBellsReadSchema

class GetAllFavoriteBellsForCharacterUseCaseProtocol(UseCaseProtocol[list[FavoriteBellsReadSchema]]):
    async def __call__(self, token: UserTokenDataReadSchema) -> list[FavoriteBellsReadSchema]:
        ...

class GetAllFavoriteBellsForCharacterUseCase(GetAllFavoriteBellsForCharacterUseCaseProtocol):
    def __init__(self, service: FavoriteBellsServiceProtocol):
        self.service = service

    async def __call__(self, token: UserTokenDataReadSchema) -> list[FavoriteBellsReadSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_all_favorite_for_character(token.character_id)