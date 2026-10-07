import logging
from datetime import UTC, datetime
from typing import Protocol

from shared.enums import MonsterAttackStatus
from shared.schemas.mining import MonsterAttackEventSchema

from .publisher_sync import RedisPublisherSyncProtocol

logger = logging.getLogger(__name__)


class MonsterEventsSyncProtocol(Protocol):
    def publish_monster_attack(self, monster_data: MonsterAttackEventSchema, event_type: MonsterAttackStatus) -> None:
        ...


class MonsterEventsSync(MonsterEventsSyncProtocol):
    def __init__(self, publisher: RedisPublisherSyncProtocol):
        self.publisher = publisher

    def publish_monster_attack(self, monster_data: MonsterAttackEventSchema, event_type: MonsterAttackStatus) -> None:
        """Синхронная публикация события атаки монстра"""
        event_data = {
            "event_type": f"monster_attack_{event_type.value}",
            "data": monster_data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        self.publisher.publish("monster_attack", event_data)
        logger.info(f"Published monster_attack event for mining {monster_data.mining_id}")

    def _get_timestamp(self) -> str:
        return datetime.now(UTC).isoformat()