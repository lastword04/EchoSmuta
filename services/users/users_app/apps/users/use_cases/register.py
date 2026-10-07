from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from shared.schemas.users import UserCreateSchema, UserReadSchema
from ..services.users import UserServiceProtocol


class RegisterUserUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(self: Self, user: UserCreateSchema) -> UserReadSchema: ...


class RegisterUserUseCase(RegisterUserUseCaseProtocol):
    def __init__(self: Self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(self: Self, user: UserCreateSchema) -> UserReadSchema:
        return await self.user_service.create(user)
