import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.item_events import ItemMessageEventSchema

from ...resources.events.publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class ItemEventsProtocol(Protocol):
    async def publish_message(self, item_message: ItemMessageEventSchema) -> None:
        ...


class ItemEvents(ItemEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_message(self, item_message: ItemMessageEventSchema) -> None:
        event_data = {
            "event_type": item_message.event_type,
            "data": item_message.model_dump(mode="json"),
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("items_events", event_data)
        logger.info("Published items event %s", item_message.event_type)

    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()
