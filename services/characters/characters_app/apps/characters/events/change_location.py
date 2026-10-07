import logging
import uuid
from typing import Protocol
from datetime import datetime, timezone
from shared.schemas.characters import CharacterChangeLocationEvent
from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)

class ChangeLocationEventsProtocol(Protocol):
    async def publish_change_location(self, data: CharacterChangeLocationEvent) -> None: 
        ...
    async def publish_room_change(
        self,
        character_id: uuid.UUID,
        name: str,
        level: int,
        race: str | None,
        old_room_slug: str,
        new_room_slug: str,
        old_real_location_slug: str | None = None,
        new_real_location_slug: str | None = None,
    ) -> None: ...

class ChangeLocationEvents(ChangeLocationEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher
    
    async def publish_change_location(self, data: CharacterChangeLocationEvent) -> None: 

        """Публикация события результата майнинга персонажа в Redis канал"""
        event_data = {
            "event_type": "change_location",
            "data": data.model_dump(mode='json'),
            "timestamp": self._get_timestamp()
        }
        await self.publisher.publish("change_location", event_data)
        logger.info(f"Published change_location event for character {data.character_id}")
    
    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def publish_room_change(
        self,
        character_id: uuid.UUID,
        name: str,
        level: int,
        race: str | None,
        old_room_slug: str,
        new_room_slug: str,
        old_real_location_slug: str | None = None,
        new_real_location_slug: str | None = None,
    ) -> None:
        """Смена «пространства» персонажа (локация или комната).

        Публикует в тот же канал 'change_location', что и publish_change_location,
        но принимает плоские slug-и вместо LocationReadSchema. Это позволяет
        использовать виртуальные идентификаторы ('house:uuid', 'inn:inside'),
        которых нет в таблице locations.

        CharacterPresenceHandler извлекает из old_location/new_location только
        поле slug, поэтому плоские dict-ы {slug: ...} он обрабатывает корректно.
        """
        event_data = {
            "event_type": "change_location",
            "data": {
                "character_id": str(character_id),
                "old_location": {"slug": old_room_slug},
                "new_location": {"slug": new_room_slug},
                "old_real_location_slug": old_real_location_slug,
                "new_real_location_slug": new_real_location_slug,
                "name": name,
                "level": level,
                "race": race,
            },
            "timestamp": self._get_timestamp(),
        }
        await self.publisher.publish("change_location", event_data)
        logger.info(
            "Published room_change for %s: %s -> %s",
            character_id, old_room_slug, new_room_slug,
        )
