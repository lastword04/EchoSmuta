import redis.asyncio as redis
from ....core.repositories.base_redis_repository import BaseRedisRepository

class FileRedisRepositoryProtocol(BaseRedisRepository[str]):
    pass

class FileRedisRepository(FileRedisRepositoryProtocol):
    """Репозиторий для работы с файлами"""

    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, prefix="files")