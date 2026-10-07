import logging
from datetime import datetime, timezone
from typing import Protocol

from shared.schemas.item_events import ItemMessageEventSchema

from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class RestEventsProtocol(Protocol):
    async def publish_message(self, item_message: ItemMessageEventSchema) -> None: ...
    async def publish_state_event(self, location_slug: str) -> None: ...


class RestEvents(RestEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_message(self, item_message: ItemMessageEventSchema) -> None:
        event_data = {
            "event_type": item_message.event_type,
            "data": item_message.model_dump(mode="json"),
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("items_events", event_data)
        logger.info("Published rest event %s", item_message.event_type)

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def publish_state_event(self, location_slug: str) -> None:
        """Публикует «в гостинице что-то изменилось»: аренда/выход/истечение.

        Отдельный канал, а не items_events: то уходит в ItemEventHandler,
        который валидирует payload против ItemMessageEventSchema и создаёт
        чат-сообщения. Здесь этого не надо — это чисто UI-сигнал.
        """
        event_data = {
            "event_type": "rest_state_updated",
            "data": {"location_slug": location_slug},
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("rest_state_events", event_data)
        logger.info("Published rest_state_updated for %s", location_slug)