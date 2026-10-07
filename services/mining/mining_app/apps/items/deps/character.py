"""Провайдеры character-домена: городской торговый магазин персонажа (CT shop)
и инвентарь персонажа.

Здесь живёт get_character_item_service — хаб зависимостей, который используют
items/shop/sale/purchase и apps/admin. Доменные модули импортируют его отсюда;
сам character.py от items.py не зависит, поэтому цикла не возникает.
"""
from fastapi import Depends

from ....settings import Settings, get_settings
from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisherProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..adapters.file_storage import FileServiceClientProtocol
from ..events.items import ItemEventsProtocol
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.crafting_license.crafting_license import (
    CraftingLicenseRepositoryProtocol,
)
from ..repositories.sale.sale_inventory_items import SaleInventoryItemRepositoryProtocol
from ..repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.character.character_items import (
    CharacterItemService,
    CharacterItemServiceProtocol,
)
from ..services.city_trading_character.city_trading import (
    CityTradingShopCharacterService,
    CityTradingShopCharacterServiceProtocol,
    UpdateCityTradingShopService,
    UpdateCityTradingShopServiceProtocol,
)
from ..services.stats.character_city_trade_stats import (
    CharacterCityTradeStatsServiceProtocol,
)
from ..use_cases.character.create import (
    CreateCTShopUseCase,
    CreateCTShopUseCaseProtocol,
)
from ..use_cases.character.get import GetCTShopByIdUseCase, GetCTShopByIdUseCaseProtocol
from ..use_cases.character.get_by_number import (
    GetCTShopByNumberUseCase,
    GetCTShopByNumberUseCaseProtocol,
)
from ..use_cases.character.get_character_items import (
    GetCharacterItemsUseCase,
    GetCharacterItemsUseCaseProtocol,
)
from ..use_cases.character.get_city_shop_for_character import (
    GetCTShopForCharacterUseCase,
    GetCTShopForCharacterUseCaseProtocol,
)
from ..use_cases.character.get_items_from_location import (
    GetItemsFromLocationUseCase,
    GetItemsFromLocationUseCaseProtocol,
)
from ..use_cases.character.get_shops_with_sale_items_paginated import (
    GetShopsWithSaleItemsPaginatedUseCase,
    GetShopsWithSaleItemsPaginatedUseCaseProtocol,
)
from ..use_cases.character.level_up_shop import (
    LevelUpCTShopUseCase,
    LevelUpCTShopUseCaseProtocol,
)
from ..use_cases.character.update_info import (
    UpdateInfoCTShopUseCase,
    UpdateInfoCTShopUseCaseProtocol,
)
from ..use_cases.character.update_license_duration import (
    UpdateLicenseCTShopUseCase,
    UpdateLicenseCTShopUseCaseProtocol,
)
from ..use_cases.character.update_photo import (
    UpdatePhotoCTShopUseCase,
    UpdatePhotoCTShopUseCaseProtocol,
)
from ..use_cases.character.upgrade_shop import (
    UpgradeCTShopUseCase,
    UpgradeCTShopUseCaseProtocol,
)
from .adapters import (
    get_character_service_client,
    get_file_service_client,
    get_item_template_service,
)
from .events import get_items_events
from .repositories import (
    _get_character_item_repository,
    _get_city_trading_shop_buy_settings_repository,
    _get_city_trading_shop_character_repository,
    _get_city_trading_shop_settings_repository,
    _get_crafting_license_repository,
    _get_sale_inventory_item_repository,
)
from .stats import get_character_city_trade_stats_service


def get_character_item_service(
    repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    shop_repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    sale_repository: SaleInventoryItemRepositoryProtocol = Depends(_get_sale_inventory_item_repository),
    settings_repository: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    crafting_license_repository: CraftingLicenseRepositoryProtocol = Depends(_get_crafting_license_repository)
) -> CharacterItemServiceProtocol:
    return CharacterItemService(
        repository=repository,
        character_client=character_client,
        shop_repository=shop_repository,
        sale_repository=sale_repository,
        settings_repository=settings_repository,
        crafting_license_repository=crafting_license_repository
    )

def get_get_character_items_use_case(
    service: CharacterItemServiceProtocol = Depends(get_character_item_service)
) -> GetCharacterItemsUseCaseProtocol:
    return GetCharacterItemsUseCase(service=service)

def get_get_items_from_location_use_case(
    service: CharacterItemServiceProtocol = Depends(get_character_item_service)
) -> GetItemsFromLocationUseCaseProtocol:
    return GetItemsFromLocationUseCase(service=service)


# city trading for character
def get_city_trading_shop_character_service(
    repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    city_settings_repo: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    city_settings_buy_repo: CityTradingShopBuySettingsRepositoryProtocol = Depends(_get_city_trading_shop_buy_settings_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    file_service: FileServiceClientProtocol = Depends(get_file_service_client),
    sale_repository: SaleInventoryItemRepositoryProtocol = Depends(_get_sale_inventory_item_repository),
    city_trade_stats_service: CharacterCityTradeStatsServiceProtocol = Depends(get_character_city_trade_stats_service),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
) -> CityTradingShopCharacterServiceProtocol:
    return CityTradingShopCharacterService(
        repository=repository,
        city_settings_repo=city_settings_repo,
        city_settings_buy_repo=city_settings_buy_repo,
        character_service=character_service,
        file_service=file_service,
        sale_repository=sale_repository,
        city_trade_stats_service=city_trade_stats_service,
        template_service=template_service,
        items_events=items_events,
    )

def get_update_city_trading_shop_service(
    repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    city_settings_repo: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    settings: Settings = Depends(get_settings),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> UpdateCityTradingShopServiceProtocol:
    return UpdateCityTradingShopService(
        repository=repository,
        city_settings_repo=city_settings_repo,
        character_service=character_service,
        template_service=template_service,
        items_events=items_events,
        redis_publisher=redis_publisher,
        license_renewal_cost=settings.city_trading_shop.license_renewal_cost,
        license_renewal_days=settings.city_trading_shop.license_renewal_days
    )

def get_get_ct_shop_for_character_use_case(
    service: CityTradingShopCharacterServiceProtocol = Depends(get_city_trading_shop_character_service)
) -> GetCTShopForCharacterUseCaseProtocol:
    return GetCTShopForCharacterUseCase(service=service)

def get_get_ct_shop_by_id_use_case(
    service: CityTradingShopCharacterServiceProtocol = Depends(get_city_trading_shop_character_service)
) -> GetCTShopByIdUseCaseProtocol:
    return GetCTShopByIdUseCase(service=service)

def get_get_ct_shop_by_number_use_case(
    service: CityTradingShopCharacterServiceProtocol = Depends(get_city_trading_shop_character_service)
) -> GetCTShopByNumberUseCaseProtocol:
    return GetCTShopByNumberUseCase(service=service)

def get_get_shops_with_sale_items_paginated_use_case(
    service: CityTradingShopCharacterServiceProtocol = Depends(get_city_trading_shop_character_service),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> GetShopsWithSaleItemsPaginatedUseCaseProtocol:
    return GetShopsWithSaleItemsPaginatedUseCase(service=service, character_client=character_client)

def get_create_ct_shop_use_case(
    service: CityTradingShopCharacterServiceProtocol = Depends(get_city_trading_shop_character_service)
) -> CreateCTShopUseCaseProtocol:
    return CreateCTShopUseCase(service=service)

def get_update_info_ct_shop_use_case(
    service: UpdateCityTradingShopServiceProtocol = Depends(get_update_city_trading_shop_service)
) -> UpdateInfoCTShopUseCaseProtocol:
    return UpdateInfoCTShopUseCase(service=service)

def get_update_license_duration_ct_shop_use_case(
    service: UpdateCityTradingShopServiceProtocol = Depends(get_update_city_trading_shop_service)
) -> UpdateLicenseCTShopUseCaseProtocol:
    return UpdateLicenseCTShopUseCase(service=service)

def get_update_photo_ct_shop_use_case(
    service: UpdateCityTradingShopServiceProtocol = Depends(get_update_city_trading_shop_service)
) -> UpdatePhotoCTShopUseCaseProtocol:
    return UpdatePhotoCTShopUseCase(service=service)

def get_level_up_ct_shop_use_case(
    service: UpdateCityTradingShopServiceProtocol = Depends(get_update_city_trading_shop_service)
) -> LevelUpCTShopUseCaseProtocol:
    return LevelUpCTShopUseCase(service=service)


def get_upgrade_ct_shop_use_case(
    repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    city_settings_repo: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> UpgradeCTShopUseCaseProtocol:
    service = UpdateCityTradingShopService(
        repository=repository,
        city_settings_repo=city_settings_repo,
        character_service=character_service,
        template_service=template_service,
        items_events=items_events,
        redis_publisher=redis_publisher,
    )
    return UpgradeCTShopUseCase(service=service)
