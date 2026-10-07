from typing import Protocol

from ...repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ...schemas import (
    CityTradingShopSettingsCreateSchema,
    CityTradingShopSettingsReadSchema,
)


class CityTradingShopSettingsServiceProtocol(Protocol):
    async def get_all(self) -> list[CityTradingShopSettingsReadSchema]:
        ...

    async def bulk_create(
        self, items: list[CityTradingShopSettingsCreateSchema]
    ) -> list[CityTradingShopSettingsReadSchema]:
        ...

class CityTradingShopSettingsService(CityTradingShopSettingsServiceProtocol):
    def __init__(self, repository: CityTradingShopSettingsRepositoryProtocol):
        self.repository = repository

    async def get_all(self) -> list[CityTradingShopSettingsReadSchema]:
        return await self.repository.get_all()

    async def bulk_create(
        self, items: list[CityTradingShopSettingsCreateSchema]
    ) -> list[CityTradingShopSettingsReadSchema]:
        return await self.repository.bulk_create(items)