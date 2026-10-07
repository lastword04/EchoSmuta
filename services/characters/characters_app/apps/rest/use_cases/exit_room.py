from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from shared.schemas.auth import UserTokenDataReadSchema
from ..services.rest_service import RestServiceProtocol


class ExitRoomUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, user: UserTokenDataReadSchema) -> None: ...


class ExitRoomUseCase(ExitRoomUseCaseProtocol):
    def __init__(self, service: RestServiceProtocol, character_repository):
        self.service = service
        self.char_repo = character_repository

    async def __call__(self, user: UserTokenDataReadSchema) -> None:
        if not user.character_id:
            from ....core.utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError()
        
        character = await self.char_repo.get(user.character_id)
        await self.service.exit_room(character)