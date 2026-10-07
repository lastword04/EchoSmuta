from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.bells import FavoriteBellsServiceProtocol

class DeleteFavoriteBellsUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, code_bell: int, token: UserTokenDataReadSchema) -> bool:
        ...

class DeleteFavoriteBellsUseCase(DeleteFavoriteBellsUseCaseProtocol):
    def __init__(self, service: FavoriteBellsServiceProtocol):
        self.service = service

    async def __call__(self, code_bell: int, token: UserTokenDataReadSchema) -> bool:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.delete(token.character_id, code_bell)