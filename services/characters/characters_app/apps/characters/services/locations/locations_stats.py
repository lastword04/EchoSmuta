from typing import Protocol
from typing_extensions import Self
from ...repositories.locations.locations_stats import LocationsStatsRepositoryProtocol
from ...schemas import LocationCharacterCountSchema


class LocationsStatsServiceProtocol(Protocol):
    async def get_character_counts_by_location(self: Self) -> list[LocationCharacterCountSchema]:
        ...

class LocationsStatsService(LocationsStatsServiceProtocol):
    def __init__(self: Self, repository: LocationsStatsRepositoryProtocol):
        self.repository = repository

    async def get_character_counts_by_location(self: Self) -> list[LocationCharacterCountSchema]:
        return await self.repository.get_character_counts_by_location()