import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.enums import MonsterAttackStatus
from shared.schemas.mining import MonsterAttackEventSchema

from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)



class MonsterEventsProtocol(Protocol):
    async def publish_monster_attack(self, monster_data: MonsterAttackEventSchema, event_type: MonsterAttackStatus) -> None: 
        ...

class MonsterEvents(MonsterEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher
    
    async def publish_monster_attack(self, monster_data: MonsterAttackEventSchema, event_type: MonsterAttackStatus) -> None: 

        """Публикация события результата майнинга персонажа в Redis канал"""
        event_data = {
            "event_type": f"monster_attack_{event_type.value}",
            "data": monster_data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        await self.publisher.publish("monster_attack", event_data)
        logger.info(f"Published mining_finished event for mining {monster_data.mining_id}")
    
    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()