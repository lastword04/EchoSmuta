import uuid
import logging
from typing import Protocol
from datetime import datetime, timezone
from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)

class CharacterEventsProtocol(Protocol):
    async def publish_character_banned(self, character_id: uuid.UUID, user_id: uuid.UUID) -> None: ...
    async def publish_character_unbanned(self, character_id: uuid.UUID, user_id: uuid.UUID) -> None: ...

class CharacterEvents(CharacterEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_character_banned(self, character_id: uuid.UUID, user_id: uuid.UUID) -> None:
        event_data = {
            "event_type": "character_banned",
            "data": {
                "character_id": str(character_id),
                "user_id": str(user_id),
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.publisher.publish("character_events", event_data)
        logger.info(f"Published character_banned event for character {character_id}")

    async def publish_character_unbanned(self, character_id: uuid.UUID, user_id: uuid.UUID) -> None:
        event_data = {
            "event_type": "character_unbanned",
            "data": {
                "character_id": str(character_id),
                "user_id": str(user_id),
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.publisher.publish("character_events", event_data)
        logger.info(f"Published character_unbanned event for character {character_id}")