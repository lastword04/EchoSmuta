import json
import logging
import asyncio
from typing import Protocol, Callable, Awaitable
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisSubscriberProtocol(Protocol):
    async def subscribe(self, channel: str, handler: Callable[[dict], Awaitable[None]]) -> None: ...
    async def unsubscribe(self, channel: str) -> None: ...


class RedisSubscriber(RedisSubscriberProtocol):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.pubsub = None
        self._running = False
        self._tasks = {}

    async def subscribe(self, channel: str, handler: Callable[[dict], Awaitable[None]]) -> None:
        """Подписка на канал с обработчиком"""
        if self.pubsub is None:
            self.pubsub = self.redis.pubsub()

        await self.pubsub.subscribe(channel)
        self._running = True

        # Запускаем обработку сообщений в фоне
        task = asyncio.create_task(self._listen_channel(channel, handler))
        self._tasks[channel] = task
        logger.info(f"Subscribed to channel: {channel}")

    async def _listen_channel(self, channel: str, handler: Callable[[dict], Awaitable[None]]):
        """Прослушивание сообщений в канале"""
        async for message in self.pubsub.listen():
            if not self._running:
                break

            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await handler(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in channel {channel}: {e}")
                except Exception as e:
                    logger.error(f"Error handling message in channel {channel}: {e}")

    async def unsubscribe(self, channel: str) -> None:
        """Отписка от канала"""
        if self.pubsub and channel in self._tasks:
            await self.pubsub.unsubscribe(channel)
            self._tasks[channel].cancel()
            del self._tasks[channel]
            logger.info(f"Unsubscribed from channel: {channel}")

    async def stop(self):
        """Остановка всех подписок"""
        self._running = False
        for channel in list(self._tasks.keys()):
            await self.unsubscribe(channel)
        if self.pubsub:
            await self.pubsub.close()