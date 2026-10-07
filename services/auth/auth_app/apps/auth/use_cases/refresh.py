from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import AuthSchema
from ..services.auth import AuthServiceProtocol 


class RefreshUseCaseProtocol(UseCaseProtocol[AuthSchema]):
    async def __call__(self: Self, token: str) -> AuthSchema:
        ...


class RefreshUseCase(RefreshUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: str) -> AuthSchema:
        return await self.service.refresh_token(token)
