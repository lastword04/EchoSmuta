"""Провайдеры репозиториев — чистые фабрики над AsyncSession.

Вынесены в общий модуль, потому что почти каждый репозиторий используется
несколькими доменами (items, character, shop, sale, purchase, crafting, recipes,
crafting_license, stats, initializators). Это делает граф зависимостей
доменных deps-модулей плоским и ациклическим.
"""
from fastapi import Depends

from ....core.db import AsyncSession, get_async_session
from ..repositories.building.building import (
    BuildingRepository,
    BuildingRepositoryProtocol,
)
from ..repositories.character.character_equipment import (
    CharacterEquipmentRepository,
    CharacterEquipmentRepositoryProtocol,
)
from ..repositories.character.character_items import (
    CharacterItemRepository,
    CharacterItemRepositoryProtocol,
)
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepository,
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.crafting.character_start_creating_item import (
    CharacterStartCreatingItemRepository,
    CharacterStartCreatingItemRepositoryProtocol,
)
from ..repositories.crafting.items_creating_action import (
    ItemsCreatingActionRepository,
    ItemsCreatingActionRepositoryProtocol,
)
from ..repositories.crafting_license.crafting_license import (
    CraftingLicenseRepository,
    CraftingLicenseRepositoryProtocol,
)
from ..repositories.items.experience_for_level import (
    ItemExperienceForLevelRepository,
    ItemExperienceForLevelRepositoryProtocol,
)
from ..repositories.items.items import ItemRepository, ItemRepositoryProtocol
from ..repositories.items.items_component import (
    ItemComponentRepository,
    ItemComponentRepositoryProtocol,
)
from ..repositories.items.items_price import (
    ItemPriceRepository,
    ItemPriceRepositoryProtocol,
)
from ..repositories.recipes.character_recipes import (
    CharacterRecipesRepository,
    CharacterRecipesRepositoryProtocol,
)
from ..repositories.sale.sale_history import SaleHistoryRepository
from ..repositories.sale.sale_inventory_items import (
    SaleInventoryItemRepository,
    SaleInventoryItemRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepository,
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepository,
    CityTradingShopSettingsRepositoryProtocol,
)
from ..repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepository,
    CharacterCityTradeStatsRepositoryProtocol,
)


# item
def _get_item_repository(session: AsyncSession = Depends(get_async_session)) -> ItemRepositoryProtocol:
    return ItemRepository(session=session)

# item component
def _get_item_component_repository(session: AsyncSession = Depends(get_async_session)) -> ItemComponentRepositoryProtocol:
    return ItemComponentRepository(session=session)

# building
def _get_building_repository(session: AsyncSession = Depends(get_async_session)) -> BuildingRepositoryProtocol:
    return BuildingRepository(session=session)

# recipes
def _get_character_recipes_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterRecipesRepositoryProtocol:
    return CharacterRecipesRepository(session=session)


# city trading shop character repository (needed by character items)
def _get_city_trading_shop_character_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CityTradingShopCharacterRepositoryProtocol:
    return CityTradingShopCharacterRepository(session=session)

# sale inventory item repository (needed by character items)
def _get_sale_inventory_item_repository(session: AsyncSession = Depends(get_async_session)) -> SaleInventoryItemRepositoryProtocol:
    return SaleInventoryItemRepository(session=session)

# character items
def _get_character_item_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterItemRepositoryProtocol:
    return CharacterItemRepository(session=session)


def _get_character_equipment_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterEquipmentRepositoryProtocol:
    return CharacterEquipmentRepository(session=session)

# city trading settings
def _get_city_trading_shop_settings_repository(session: AsyncSession = Depends(get_async_session)) -> CityTradingShopSettingsRepositoryProtocol:
    return CityTradingShopSettingsRepository(session=session)

# city trading buy settings
def _get_city_trading_shop_buy_settings_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CityTradingShopBuySettingsRepositoryProtocol:
    return CityTradingShopBuySettingsRepository(session=session)


# crafting license
def _get_crafting_license_repository(session: AsyncSession = Depends(get_async_session)) -> CraftingLicenseRepositoryProtocol:
    return CraftingLicenseRepository(session=session)


# item price
def _get_item_price_repository(session: AsyncSession = Depends(get_async_session)) -> ItemPriceRepositoryProtocol:
    return ItemPriceRepository(session=session)


# character city trade stats
def _get_character_city_trade_stats_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterCityTradeStatsRepositoryProtocol:
    return CharacterCityTradeStatsRepository(session=session)


# история продаж
def get_sale_history_repository(session: AsyncSession = Depends(get_async_session)) -> SaleHistoryRepository:
    return SaleHistoryRepository(session)


# experience for level
def _get_item_experience_for_level_repository(session: AsyncSession = Depends(get_async_session)) -> ItemExperienceForLevelRepositoryProtocol:
    return ItemExperienceForLevelRepository(session=session)


# character start creating item
def _get_character_start_creating_item_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CharacterStartCreatingItemRepositoryProtocol:
    return CharacterStartCreatingItemRepository(session=session)


# Items Creating Actions
def _get_items_creating_action_repository(
    session: AsyncSession = Depends(get_async_session)
) -> ItemsCreatingActionRepositoryProtocol:
    return ItemsCreatingActionRepository(session=session)
