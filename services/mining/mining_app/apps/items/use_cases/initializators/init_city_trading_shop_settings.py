from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import (
    CityTradingShopSettingsCreateSchema,
    CityTradingShopSettingsReadSchema,
)
from ...services.settings.city_trading_shop_settings import (
    CityTradingShopSettingsServiceProtocol,
)

ShopData = tuple[int, int, float, int | None]

class InitializeCityTradingShopSettingsUseCaseProtocol(UseCaseProtocol[list[CityTradingShopSettingsReadSchema]]):
    async def __call__(self: Self) -> list[CityTradingShopSettingsReadSchema]:
        ...


class InitializeCityTradingShopSettingsUseCase(InitializeCityTradingShopSettingsUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[CityTradingShopSettingsReadSchema]:
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
            raise ValueError("City trading shop settings count is incorrect.")

        # Если нет записей, создаём все эталонные
        return await self.service.bulk_create(default_settings)

    def _get_default_settings(self: Self) -> list[CityTradingShopSettingsCreateSchema]:
        # Структура данных: (level, capacity, tax_percent, upgrade_cost_in_dt)
        pharmacy_levels: list[ShopData] = [
            (0, 200, 7.5, 53),
            (1, 275, 7.0, 61),
            (2, 350, 6.5, 69),
            (3, 425, 6.0, 77),
            (4, 500, 5.5, 85),
            (5, 575, 5.0, 93),
            (6, 650, 4.5, 101),
            (7, 725, 4.0, 109),
            (8, 800, 3.5, 117),
            (9, 875, 3.25, 125),
            (10, 950, 3.0, None), # Уровень 10 не требует стоимости для апгрейда
        ]

        pet_nursery_levels: list[ShopData] = [
            (0, 5, 7.5, 25),
            (1, 7, 7.0, 30),
            (2, 9, 6.5, 35),
            (3, 11, 6.0, 40),
            (4, 13, 5.5, 45),
            (5, 15, 5.0, 50),
            (6, 17, 4.5, 55),
            (7, 19, 4.0, 60),
            (8, 21, 3.5, 65),
            (9, 23, 3.25, 70),
            (10, 25, 3.0, None),
        ]

        hunting_shop_levels: list[ShopData] = [
            (0, 200, 7.5, 53),
            (1, 250, 7.0, 61),
            (2, 300, 6.5, 69),
            (3, 350, 6.0, 77),
            (4, 400, 5.5, 85),
            (5, 450, 5.0, 93),
            (6, 500, 4.5, 101),
            (7, 550, 4.0, 109),
            (8, 600, 3.5, 117),
            (9, 650, 3.25, 125),
            (10, 700, 3.0, None),
        ]

        fish_shop_levels: list[ShopData] = [
            (0, 200, 7.5, 53),
            (1, 250, 7.0, 61),
            (2, 300, 6.5, 69),
            (3, 350, 6.0, 77),
            (4, 400, 5.5, 85),
            (5, 450, 5.0, 93),
            (6, 500, 4.5, 101),
            (7, 550, 4.0, 109),
            (8, 600, 3.5, 117),
            (9, 650, 3.25, 125),
            (10, 700, 3.0, None),
        ]

        furniture_shop_levels: list[ShopData] = [
            (0, 600, 7.5, 77),
            (1, 800, 7.0, 89),
            (2, 1000, 6.5, 101),
            (3, 1200, 6.0, 113),
            (4, 1400, 5.5, 125),
            (5, 1600, 5.0, 137),
            (6, 1800, 4.5, 149),
            (7, 2000, 4.0, 161),
            (8, 2200, 3.5, 173),
            (9, 2400, 3.25, 185),
            (10, 2600, 3.0, None),
        ]

        trade_hall_levels: list[ShopData] = [
            (0, 1000, 7.5, 150),
            (1, 1750, 7.0, 175),
            (2, 2500, 6.5, 200),
            (3, 3250, 6.0, 225),
            (4, 4000, 5.5, 250),
            (5, 4750, 5.0, 275),
            (6, 5500, 4.5, 300),
            (7, 6250, 4.0, 325),
            (8, 7000, 3.5, 350),
            (9, 7750, 3.25, 375),
            (10, 8500, 3.0, None),
        ]


        all_settings = []
        # Собираем настройки для каждой локации
        for level, capacity, tax_percent, cost in pharmacy_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.9.pharmacy", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )
        
        for level, capacity, tax_percent, cost in pet_nursery_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.24.bird-market", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )

        for level, capacity, tax_percent, cost in hunting_shop_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.22.hunting-shop", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )

        for level, capacity, tax_percent, cost in fish_shop_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.25.fish-shop", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )

        for level, capacity, tax_percent, cost in furniture_shop_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.21.furniture-shop", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )

        for level, capacity, tax_percent, cost in trade_hall_levels:
            all_settings.append(
                CityTradingShopSettingsCreateSchema(
                    location_slug="1.27.trade-hall", # Указанная локация
                    level=level,
                    capacity=capacity,
                    tax=tax_percent / 100,
                    price_up_level=cost
                )
            )

        return all_settings
