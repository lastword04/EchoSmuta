import uuid
from .....core.use_cases import UseCaseProtocol
from ...services.rate_limit import RateLimitServiceProtocol

class RateLimitUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, character_id: uuid.UUID) -> bool:
        ...

class RateLimitUseCase(RateLimitUseCaseProtocol):
    def __init__(self, rate_limiter: RateLimitServiceProtocol):
        self.rate_limiter = rate_limiter

    async def __call__(self, character_id: uuid.UUID) -> bool:
        return await self.rate_limiter.is_allowed(character_id)