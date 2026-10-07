import redis.asyncio as redis
from ....core.repositories.base_redis_repository import BaseRedisRepository

class CaptchaRedisRepositoryProtocol(BaseRedisRepository[str]):
    pass

class CaptchaRedisRepository(CaptchaRedisRepositoryProtocol):
    """Репозиторий для работы с капчей"""
    
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, prefix="captcha")