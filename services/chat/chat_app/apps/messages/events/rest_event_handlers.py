import logging
from typing import Awaitable, Protocol

from .subscriber import RedisSubscriberProtocol
from ..services.publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class RestEventHandlerProtocol(Protocol):
    async def handle_rest_event(self, event_data: dict) -> Awaitable[None]: ...
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class RestEventHandler(RestEventHandlerProtocol):
    def __init__(self, subscriber: RedisSubscriberProtocol, publisher: RedisPublisherProtocol):
        self.subscriber = subscriber
        self.publisher = publisher
        self._is_listening = False

    async def handle_rest_event(self, event_data: dict) -> None:
        try:
            event_type = event_data.get("event_type")
            # Broadcast всем подключённым: frontend сам отфильтрует по локации
            # (он сверяет location_slug из data со своей локацией).
            await self.publisher.publish("chat_room_rest", event_data)
            logger.debug("Rest event %s forwarded", event_type)
        except Exception as e:
            logger.error("Unexpected error handling rest event: %s", e)

    async def start_listening(self) -> None:
        if self._is_listening:
            return
        await self.subscriber.subscribe("rest_state_events", self._route_event)
        self._is_listening = True
        logger.info("Started listening for rest events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return
        if hasattr(self.subscriber, "stop"):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, "unsubscribe"):
            await self.subscriber.unsubscribe("rest_state_events")
        self._is_listening = False
        logger.info("Stopped listening for rest events")

    async def _route_event(self, event_data: dict) -> None:
        if not event_data.get("event_type"):
            return
        await self.handle_rest_event(event_data)