import uuid
from typing_extensions import Self
from shared.schemas.users import UserReadSchema, PasswordSchema
from ....core.use_cases import UseCaseProtocol
from ..services.users import UserServiceProtocol


class ChangePasswordUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(
        self: Self, user_id: uuid.UUID, password: PasswordSchema
    ) -> UserReadSchema: ...


class ChangePasswordUseCase(ChangePasswordUseCaseProtocol):
    def __init__(self: Self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(
        self: Self, user_id: uuid.UUID, password: PasswordSchema
    ) -> UserReadSchema:
        return await self.user_service.change_password(user_id, password)
