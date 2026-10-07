from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import (
    CityTradingShopBuySettingsCreateSchema,
    CityTradingShopBuySettingsReadSchema,
)
from ...services.settings.city_trading_shop_settings import (
    CityTradingShopSettingsServiceProtocol,
)


class InitializeCityTradingShopBuySettingsUseCaseProtocol(UseCaseProtocol[list[CityTradingShopBuySettingsReadSchema]]):
    async def __call__(self: Self) -> list[CityTradingShopBuySettingsReadSchema]:
        ...


class InitializeCityTradingShopBuySettingsUseCase(InitializeCityTradingShopBuySettingsUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[CityTradingShopBuySettingsReadSchema]:
        # Получаем текущие записи
        current_settings = await self.service.get_all()
        
        # Получаем эталонные данные
        default_settings = self._get_default_settings()
        
        expected_count = len(default_settings)
        
        # Проверяем, совпадает ли количество
        if len(current_settings) == expected_count:
            # Данные уже инициализированы, возвращаем
            return current_settings
        
        if len(current_settings) != 0:
            # Если есть какие-то записи, но их неожиданное количество - ошибка
            raise ValueError("City trading shop buy settings count is incorrect.")

        # Если нет записей, создаём все эталонные
        return await self.service.bulk_create(default_settings)

    def _get_default_settings(self: Self) -> list[CityTradingShopBuySettingsCreateSchema]:
        
        settings_data = [
            # location_slug, min_level, price
            ("1.9.pharmacy", 5, 250),
            ("1.25.fish-shop", 5, 250),
            ("1.21.furniture-shop", 5, 250),
            ("1.16.jewelers", 7, 500),
            ("1.13.forge", 6, 500),
            ("1.22.hunting-shop", 3, 200),
            ("1.24.bird-market", 3, 200),
            ("1.27.trade-hall", 3, 200),
        ]

        return [
            CityTradingShopBuySettingsCreateSchema(
                location_slug=s_location_slug,
                min_level=s_min_level,
                price=s_price
            )
            for s_location_slug, s_min_level, s_price in settings_data
        ]
