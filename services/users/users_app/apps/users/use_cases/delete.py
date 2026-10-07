import uuid
from shared.schemas.users import UserReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.users import UserServiceProtocol


class DeleteUserUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(self, user_id: uuid.UUID) -> UserReadSchema: ...


class DeleteUserUseCase(DeleteUserUseCaseProtocol):
    def __init__(self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(self, user_id: uuid.UUID) -> UserReadSchema:
        return await self.user_service.delete(user_id)
