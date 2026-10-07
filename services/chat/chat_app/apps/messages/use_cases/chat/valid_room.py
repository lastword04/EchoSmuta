from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.room_checker import RoomCheckerProtocol

class ValidRoomUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, room: str, token: UserTokenDataReadSchema) -> bool:
        ...

class ValidRoomUseCase(ValidRoomUseCaseProtocol):
    def __init__(self, room_checker: RoomCheckerProtocol):
        self.room_checker = room_checker

    async def __call__(self, room: str, token: UserTokenDataReadSchema) -> bool:
        return await self.room_checker.is_room_valid(room, token.role)