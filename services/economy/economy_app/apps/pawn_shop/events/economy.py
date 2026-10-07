import logging
from datetime import datetime, timezone
from typing import Protocol

from shared.schemas.item_events import ItemMessageEventSchema

from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class EconomyEventsProtocol(Protocol):
    async def publish_message(self, item_message: ItemMessageEventSchema) -> None:
        ...

    async def publish_state_update(self, event_type: str, payload: dict) -> None:
        ...


class EconomyEvents(EconomyEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_message(self, item_message: ItemMessageEventSchema) -> None:
        event_data = {
            "event_type": item_message.event_type,
            "data": item_message.model_dump(mode="json"),
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("items_events", event_data)
        logger.info("Published economy event %s", item_message.event_type)

    async def publish_state_update(self, event_type: str, payload: dict) -> None:
        """Событие «состояние рынка изменилось». Летит в свой канал,
        его слушает WebSocketManager и рассылает игрокам по фильтрам."""
        event_data = {
            "event_type": event_type,
            "data": payload,
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("economy_state_updated", event_data)
        logger.info("Published state update %s", event_type)

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()