import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.mining import MiningActionEventSchema

from .publisher_sync import RedisPublisherSyncProtocol

logger = logging.getLogger(__name__)


class MiningEventsSyncProtocol(Protocol):
    def publish_mining_result(self, mining_data: MiningActionEventSchema) -> None:
        ...


class MiningEventsSync(MiningEventsSyncProtocol):
    def __init__(self, publisher: RedisPublisherSyncProtocol):
        self.publisher = publisher

    def publish_mining_result(self, mining_data: MiningActionEventSchema) -> None:
        """Синхронная публикация события результата майнинга"""
        event_data = {
            "event_type": "mining_finished",
            "data": mining_data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        self.publisher.publish("mining_finished", event_data)
        logger.info(f"Published mining_finished event for mining {mining_data.id}")

    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()