from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.utils.exceptions import PermissionDeniedError
from ....core.use_cases import UseCaseProtocol 
from ..adapters.characters import CharacterServiceClientProtocol


class AuthForumUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, token_data: UserTokenDataReadSchema) -> None:

        ...


class AuthForumUseCase(AuthForumUseCaseProtocol):
    def __init__(self: Self, character_client: CharacterServiceClientProtocol):
        self.character_client = character_client

    async def __call__(self: Self, token_data: UserTokenDataReadSchema) -> None:
        if not token_data.is_main:
            raise PermissionDeniedError()
        return None