from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..services.tokens import CleanupRefreshTokenServiceProtocol 


class CleanupRefreshTokenUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self) -> bool:
        ...


class CleanupRefreshTokenUseCase(CleanupRefreshTokenUseCaseProtocol):
    def __init__(self: Self, service: CleanupRefreshTokenServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> bool:
        return await self.service.delete_all_expired_tokens()
