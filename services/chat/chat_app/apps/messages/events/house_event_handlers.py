import logging
import asyncio
from typing import Awaitable, Protocol

from .subscriber import RedisSubscriberProtocol
from ..services.publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class HouseEventHandlerProtocol(Protocol):
    async def handle_house_event(self, event_data: dict) -> Awaitable[None]: ...
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class HouseEventHandler(HouseEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        publisher: RedisPublisherProtocol,
    ):
        self.subscriber = subscriber
        self.publisher = publisher
        self._is_listening = False

    async def handle_house_event(self, event_data: dict) -> None:
        try:
            event_type = event_data.get("event_type")
            data = event_data.get("data", {})
            target_user_ids = data.get("target_user_ids", [])

            # Рассылаем каждому target_user отдельно
            for target_id in target_user_ids:
                message = {
                    "event_type": event_type,
                    "data": data,
                    "target_character_id": str(target_id),
                }
                await self.publisher.publish("chat_room_house", message)

            logger.debug(
                "House event %s forwarded to %d users",
                event_type,
                len(target_user_ids),
            )

        except Exception as e:
            logger.error("Unexpected error handling house event: %s", e)

    async def start_listening(self) -> None:
        if self._is_listening:
            return
        await self.subscriber.subscribe("house_events", self._route_event)
        self._is_listening = True
        logger.info("Started listening for house events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return
        if hasattr(self.subscriber, "stop"):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, "unsubscribe"):
            await self.subscriber.unsubscribe("house_events")
        self._is_listening = False
        logger.info("Stopped listening for house events")

    async def _route_event(self, event_data: dict) -> None:
        event_type = event_data.get("event_type")
        if not event_type:
            logger.warning("House event without event_type: %s", event_data)
            return
        await self.handle_house_event(event_data)