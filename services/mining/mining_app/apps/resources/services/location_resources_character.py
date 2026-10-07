import uuid
from typing import Protocol, Self

from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.location_character_expierence import CharacterLocationStatsRepositoryProtocol
from ..repositories.location_resources_character import LocationResourcesCharacterRepositoryProtocol
from ..schemas import LocationResourcesAndCharacterStats, ResourseCharacterResponse


class LocationResourcesCharacterServiceProtocol(Protocol):
    async def get_resources_with_amount_by_character(
        self: Self,
        character_id: uuid.UUID,
        location_slug: str | None = None,
    ) -> LocationResourcesAndCharacterStats:
        ...

    async def get_all_my(self: Self, character_id: uuid.UUID) -> list[ResourseCharacterResponse]:
        ...

class LocationResourcesCharacterService(LocationResourcesCharacterServiceProtocol):
    def __init__(
        self: Self,
        repository: LocationResourcesCharacterRepositoryProtocol,
        character_service_client: CharacterServiceClientProtocol,
        location_character_expierence_repository: CharacterLocationStatsRepositoryProtocol
    ):
        self.repository = repository
        self.character_service_client = character_service_client
        self.location_character_expierence_repository = location_character_expierence_repository

    async def get_resources_with_amount_by_character(
        self: Self,
        character_id: uuid.UUID,
        location_slug: str | None = None,
    ) -> LocationResourcesAndCharacterStats:
        # Явный slug имеет приоритет; иначе — fallback на сессию.
        # И экономим лишний вызов character-сервиса, если фронт передал slug.
        if location_slug is None:
            character_info = await self.character_service_client.get_simple_info_character(
                character_id=character_id
            )
            location_slug = character_info.location_slug

        location_resources = await self.repository.get_with_character_amounts(
            location_slug=location_slug,
            character_id=character_id,
        )

        character_expierence = await self.location_character_expierence_repository.get_or_create(
            character_id=character_id,
            location_slug=location_slug,
        )

        return LocationResourcesAndCharacterStats(
            resources=location_resources,
            character_location_level=character_expierence,
        )

    async def get_all_my(self: Self, character_id: uuid.UUID) -> list[ResourseCharacterResponse]:
        return await self.repository.get_all_my(character_id)