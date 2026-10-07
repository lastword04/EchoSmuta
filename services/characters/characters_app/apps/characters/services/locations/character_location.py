import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema, CharacterChangeLocationEvent
from ...repositories.locations.locations import LocationRepositoryProtocol
from ...repositories.character.characters import CharacterRepositoryProtocol
from ...events.change_location import ChangeLocationEventsProtocol

class CharacterLocationServiceProtocol(Protocol):
    async def update_character_location(
        self: Self,
        character_id: uuid.UUID,
        location_slug: str
    ) -> CharacterReadSchema:
        ...

class CharacterLocationService(CharacterLocationServiceProtocol):
    def __init__(
        self: Self,
        location_repository: LocationRepositoryProtocol,
        character_repository: CharacterRepositoryProtocol,
        character_location_event: ChangeLocationEventsProtocol
    ):
        self.location_repository = location_repository
        self.character_repository = character_repository
        self.character_location_event = character_location_event

    async def update_character_location(
        self: Self,
        character_id: uuid.UUID,
        location_slug: str
    ) -> CharacterReadSchema:
        old_location = await self.location_repository.get_location_for_character(character_id)
        if old_location.slug != location_slug:
            new_location = await self.location_repository.get_by_slug(location_slug)

            # Читаем персонажа ДО обновления — нужен его current_room_id и name/level/race
            character_before = await self.character_repository.get(character_id)

            updated_character = await self.character_repository.update_location_slug_by_character(
                character_id=character_id,
                location_slug=location_slug
            )

            # Смена локации через карту всегда выкидывает из виртуальной комнаты
            # (дома/номера). Если игрок был в комнате — сбрасываем её.
            if character_before.current_room_id is not None:
                await self.character_repository.update_current_room_id(character_id, None)

            # «Старое пространство» для события: виртуальная комната, если была, иначе локация.
            # Это критично: чат должен отписаться ИМЕННО от того канала, на который он подписан.
            old_room_slug = character_before.current_room_id or old_location.slug

            await self.character_location_event.publish_room_change(
                character_id=updated_character.id,
                name=updated_character.name,
                level=updated_character.level,
                race=updated_character.race.value if updated_character.race else None,
                old_room_slug=old_room_slug,
                new_room_slug=location_slug,
                old_real_location_slug=character_before.location_slug,
                new_real_location_slug=location_slug,
            )

            return updated_character
        else:
            return await self.character_repository.get(character_id)