import json
import logging
import asyncio
from typing import Protocol, Callable, Awaitable
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisSubscriberProtocol(Protocol):
    async def subscribe(self, channel: str, handler: Callable[[dict], Awaitable[None]]) -> None:
        ...
    async def unsubscribe(self, channel: str) -> None:
        ...


class RedisSubscriber(RedisSubscriberProtocol):
    """Один pubsub = один task, сообщения роутятся по имени канала.

    Раньше на каждый канал создавалась отдельная корутина, итерирующая один и
    тот же ``self.pubsub.listen()``. Сообщения из всех каналов распределялись
    между корутинами случайно — события терялись и дублировались. Теперь один
    ``_listen``-цикл читает `pubsub.listen()` и диспетчеризует сообщение в
    нужный обработчик по ``message["channel"]``.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._pubsub = None
        self._handlers: dict[str, Callable[[dict], Awaitable[None]]] = {}
        self._listen_task: asyncio.Task | None = None

    async def subscribe(self, channel: str, handler: Callable[[dict], Awaitable[None]]) -> None:
        """Подписка на канал с обработчиком."""
        self._handlers[channel] = handler
        if self._pubsub is None:
            self._pubsub = self.redis.pubsub()
        await self._pubsub.subscribe(channel)

        if self._listen_task is None or self._listen_task.done():
            self._listen_task = asyncio.create_task(self._listen())

        logger.info("Subscribed to channel: %s", channel)

    async def _listen(self) -> None:
        """Единственный слушатель всех каналов pubsub; роутинг по имени канала."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue

                channel = message.get("channel")
                if not channel:
                    continue

                handler = self._handlers.get(channel)
                if handler is None:
                    logger.debug("No handler for channel %s", channel)
                    continue

                try:
                    data = json.loads(message["data"])
                    await handler(data)
                except json.JSONDecodeError as e:
                    logger.error("JSON decode error in channel %s: %s", channel, e)
                except Exception as e:
                    logger.error("Error handling message in channel %s: %s", channel, e)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("RedisSubscriber listen error: %s", e)

    async def unsubscribe(self, channel: str) -> None:
        """Отписка от канала."""
        if channel not in self._handlers:
            return

        del self._handlers[channel]
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)

        # Если обработчиков не осталось — останавливаем единственный цикл
        if not self._handlers and self._listen_task:
            task = self._listen_task
            self._listen_task = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("Unsubscribed from channel: %s", channel)

    async def stop(self):
        """Остановка всех подписок и закрытие pubsub."""
        for channel in list(self._handlers.keys()):
            await self.unsubscribe(channel)

        if self._pubsub:
            try:
                await self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None

        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None