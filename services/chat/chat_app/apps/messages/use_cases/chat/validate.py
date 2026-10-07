from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .valid_room import ValidRoomUseCaseProtocol
from .valid_token import ValidTokenUseCaseProtocol

class ValidateConnectProtocol(UseCaseProtocol[UserTokenDataReadSchema]):
    async def __call__(self, token: str, room: str) -> UserTokenDataReadSchema:
        ...

class ValidateConnect(ValidateConnectProtocol):
    def __init__(self, valid_token: ValidTokenUseCaseProtocol,
                 valid_room: ValidRoomUseCaseProtocol) -> UserTokenDataReadSchema:
        self.valid_token = valid_token
        self.valid_room = valid_room

    async def __call__(self, token: str, room: str) -> UserTokenDataReadSchema:
        user_data = await self.valid_token(token)
        await self.valid_room(room, user_data)
        return user_data