import uuid
from typing import Protocol

from ...repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepositoryProtocol,
)
from ...schemas import (
    CharacterCityTradeStatsCreateSchema,
    CharacterCityTradeStatsReadSchema,
)


class CharacterCityTradeStatsServiceProtocol(Protocol):
    async def create(self, data: CharacterCityTradeStatsCreateSchema) -> CharacterCityTradeStatsReadSchema:
        ...

    async def get_or_create(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema:
        ...


class CharacterCityTradeStatsService(CharacterCityTradeStatsServiceProtocol):
    def __init__(self, repository: CharacterCityTradeStatsRepositoryProtocol):
        self.repository = repository

    async def create(self, data: CharacterCityTradeStatsCreateSchema) -> CharacterCityTradeStatsReadSchema:
        return await self.repository.create(data)

    async def get_or_create(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema:
        existing = await self.repository.get_by_character_and_location(character_id, location_slug)
        if existing:
            return existing
        
        data = CharacterCityTradeStatsCreateSchema(
            character_id=character_id,
            location_slug=location_slug
        )
        return await self.repository.create(data)
