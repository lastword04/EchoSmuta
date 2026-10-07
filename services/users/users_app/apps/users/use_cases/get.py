import uuid
from shared.schemas.users import UserReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.users import UserServiceProtocol


class GetUserUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(self, user_id: uuid.UUID) -> UserReadSchema: ...


class GetUserUseCase(GetUserUseCaseProtocol):
    def __init__(self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(self, user_id: uuid.UUID) -> UserReadSchema:
        return await self.user_service.get(user_id)
