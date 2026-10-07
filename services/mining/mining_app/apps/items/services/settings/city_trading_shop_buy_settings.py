import uuid
from typing import Protocol

from ...adapters.characters import CharacterServiceClientProtocol
from ...repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ...schemas import (
    CityTradingShopBuySettingsCreateSchema,
    CityTradingShopBuySettingsReadSchema,
)


class CityTradingShopBuySettingsServiceProtocol(Protocol):
    async def get_all(self) -> list[CityTradingShopBuySettingsReadSchema]:
        ...

    async def bulk_create(
        self, items: list[CityTradingShopBuySettingsCreateSchema]
    ) -> list[CityTradingShopBuySettingsReadSchema]:
        ...

    async def get_by_location_slug(self, location_slug: str) -> CityTradingShopBuySettingsReadSchema:
        ...

class CityTradingShopBuySettingsService(CityTradingShopBuySettingsServiceProtocol):
    def __init__(self, repository: CityTradingShopBuySettingsRepositoryProtocol):
        self.repository = repository

    async def get_all(self) -> list[CityTradingShopBuySettingsReadSchema]:
        return await self.repository.get_all()

    async def bulk_create(
        self, items: list[CityTradingShopBuySettingsCreateSchema]
    ) -> list[CityTradingShopBuySettingsReadSchema]:
        return await self.repository.bulk_create(items)
    
    async def get_by_location_slug(self, location_slug: str) -> CityTradingShopBuySettingsReadSchema:
        return await self.repository.get_by_location_slug(location_slug)
    
class CityTradingShopBuySettingsForCharacterServiceProtocol(Protocol):
    async def get_by_character_id(self, character_id: uuid.UUID) -> CityTradingShopBuySettingsReadSchema:
        ...


class CityTradingShopBuySettingsForCharacterService(CityTradingShopBuySettingsForCharacterServiceProtocol):
    def __init__(self, crud_service: CityTradingShopBuySettingsServiceProtocol,
                 character_service: CharacterServiceClientProtocol):
        self.crud_service = crud_service
        self.character_service = character_service

    async def get_by_character_id(self, character_id: uuid.UUID) -> CityTradingShopBuySettingsReadSchema:
        character = await self.character_service.get_simple_character_balance(character_id)
        return await self.crud_service.get_by_location_slug(character.location_slug)
