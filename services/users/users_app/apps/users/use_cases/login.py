from ....core.use_cases import UseCaseProtocol
from shared.schemas.users import UserLoginSchema, UserReadSchema
from ..services.users import UserServiceProtocol


class LoginUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(self, user: UserLoginSchema) -> UserReadSchema: ...


class LoginUseCase(LoginUseCaseProtocol):
    def __init__(self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(self, user: UserLoginSchema) -> UserReadSchema:
        return await self.user_service.authenticate_user(user)
