import logging
import uuid
from typing import Protocol
from datetime import datetime, timezone
from shared.schemas.characters import CharacterReadSchema 
from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)

class CharacterEventsProtocol(Protocol):
    async def publish_character_played(self, character_data: CharacterReadSchema) -> None: 
        ...

    async def publish_character_quit(self, character_id: uuid.UUID) -> None:
        ...

class CharacterEvents(CharacterEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher
    
    async def publish_character_played(self, character_data: CharacterReadSchema) -> None: 

        """Публикация события захода персонажа в игру"""
        event_data = {
            "event_type": "character_played",
            "data": character_data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        await self.publisher.publish("character_events", event_data)
        logger.info(f"Published character_played event for character {character_data.id}")
    
    async def publish_character_quit(self, character_id: uuid.UUID) -> None:
        """Публикация события выхода персонажа из игры"""
         
        event_data = {
            "event_type": "quit",
            "data": str(character_id),
            "timestamp": self._get_timestamp()
        }
        await self.publisher.publish("change_location", event_data)
        logger.info(f"Published quit event for character {character_id}")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()