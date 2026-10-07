import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.mining import MiningActionEventSchema

from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)

class MiningEventsProtocol(Protocol):
    async def publish_mining_result(self, mining_data: MiningActionEventSchema) -> None: 
        ...

class MiningEvents(MiningEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher
    
    async def publish_mining_result(self, mining_data: MiningActionEventSchema) -> None: 

        """Публикация события результата майнинга персонажа в Redis канал"""
        event_data = {
            "event_type": "mining_finished",
            "data": mining_data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        await self.publisher.publish("mining_finished", event_data)
        logger.info(f"Published mining_finished event for mining {mining_data.id}")
    
    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()