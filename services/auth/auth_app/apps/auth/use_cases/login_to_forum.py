from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import LoginSchema, AuthSchema
from ..services.auth import AuthServiceProtocol 


class LoginForumUseCaseProtocol(UseCaseProtocol[AuthSchema]):
    async def __call__(self: Self, data: LoginSchema) -> AuthSchema:
        ...


class LoginForumUseCase(LoginForumUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: LoginSchema) -> AuthSchema:
        return await self.service.login_to_forum(data)
