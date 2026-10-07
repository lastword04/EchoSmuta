from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.activity.activity import CleanupOldActivityServiceProtocol 


class CleanupActivityUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self) -> bool:
        ...


class CleanupActivityUseCase(CleanupActivityUseCaseProtocol):
    def __init__(self: Self, service: CleanupOldActivityServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> bool:
        return await self.service.cleanup_old_activity()
