import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.deal_events import DealEventSchema

from ...resources.events.publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class DealEventsProtocol(Protocol):
    async def publish_deal_event(self, event: DealEventSchema) -> None:
        ...


class DealEvents(DealEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_deal_event(self, event: DealEventSchema) -> None:
        event_data = {
            "event_type": event.event_type.value,
            "data": event.model_dump(mode="json"),
            "timestamp": self._get_timestamp(),
        }
        # Публикуем в канал deals_events
        await self.publisher.publish("deals_events", event_data)
        logger.info("Published deal event %s for deal %s", event.event_type.value, event.deal_id)

    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()