import json
import logging
from typing import Protocol

import redis  # Синхронный redis

logger = logging.getLogger(__name__)


class RedisPublisherSyncProtocol(Protocol):
    def publish(self, channel: str, message: dict) -> None: ...
    def close(self) -> None: ...


class RedisPublisherSync(RedisPublisherSyncProtocol):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def publish(self, channel: str, message: dict) -> None:
        """Синхронная публикация сообщения в Redis канал"""
        try:
            self.redis.publish(channel, json.dumps(message))
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise

    def close(self) -> None:
        """Закрытие Redis соединения"""
        try:
            self.redis.close()
            logger.debug("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()