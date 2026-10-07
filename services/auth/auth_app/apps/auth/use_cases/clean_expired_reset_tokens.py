from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..services.tokens import CleanupResetPasswordServiceProtocol 


class CleanupResetTokenUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self) -> bool:
        ...


class CleanupResetTokenUseCase(CleanupResetTokenUseCaseProtocol):
    def __init__(self: Self, service: CleanupResetPasswordServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> bool:
        return await self.service.delete_all_expired_tokens()
