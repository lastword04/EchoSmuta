"""Провайдеры инициализаторов (use_cases/initializators/).

get_building_service живёт здесь, т.к. его единственный потребитель —
get_init_buildings_use_case. Провайдер репозитория _get_building_repository
лежит в deps/repositories.py: его напрямую используют recipes и crafting.

Обратите внимание: get_item_service/get_item_component_service, вызванные
позиционно с одним аргументом, оставляют второй параметр в его Depends-значении —
это исходное поведение, сохранено 1:1.
"""
from fastapi import Depends

from ....core.db import AsyncSession, get_async_session
from ..repositories.building.building import BuildingRepositoryProtocol
from ..services.building.building import BuildingService, BuildingServiceProtocol
from ..use_cases.initializators.init_buildings import (
    InitializeBuildingsUseCase,
    InitializeBuildingsUseCaseProtocol,
)
from ..use_cases.initializators.init_city_trading_shop_buy_settings import (
    InitializeCityTradingShopBuySettingsUseCase,
    InitializeCityTradingShopBuySettingsUseCaseProtocol,
)
from ..use_cases.initializators.init_city_trading_shop_settings import (
    InitializeCityTradingShopSettingsUseCase,
    InitializeCityTradingShopSettingsUseCaseProtocol,
)
from ..use_cases.initializators.init_experience_for_level import (
    InitializeItemExperienceForLevelUseCase,
    InitializeItemExperienceForLevelUseCaseProtocol,
)
from ..use_cases.initializators.init_items import (
    InitializeItemsUseCase,
    InitializeItemsUseCaseProtocol,
)
from ..use_cases.initializators.init_items_component import (
    InitializeItemsComponentUseCase,
    InitializeItemsComponentUseCaseProtocol,
)
from ..use_cases.initializators.init_items_price import (
    InitializeItemsPriceUseCase,
    InitializeItemsPriceUseCaseProtocol,
)
from .items import (
    get_item_component_service,
    get_item_experience_for_level_service,
    get_item_price_service,
    get_item_service,
)
from .repositories import (
    _get_building_repository,
    _get_city_trading_shop_buy_settings_repository,
    _get_city_trading_shop_settings_repository,
    _get_item_component_repository,
    _get_item_experience_for_level_repository,
    _get_item_price_repository,
    _get_item_repository,
)
from .settings import (
    get_city_trading_shop_buy_settings_service,
    get_city_trading_shop_settings_service,
)


# item service and use cases
def get_init_items_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeItemsUseCaseProtocol:
    item_repo = _get_item_repository(session)
    item_service = get_item_service(item_repo)
    return InitializeItemsUseCase(item_service)


def get_init_city_trading_shop_buy_settings_use_case(
    session: AsyncSession = Depends(get_async_session),
) -> InitializeCityTradingShopBuySettingsUseCaseProtocol:
    repo = _get_city_trading_shop_buy_settings_repository(session=session)
    service = get_city_trading_shop_buy_settings_service(repository=repo)
    return InitializeCityTradingShopBuySettingsUseCase(service=service)


# item price
def get_init_items_price_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeItemsPriceUseCaseProtocol:
    items_price_repo = _get_item_price_repository(session=session)
    items_price_service = get_item_price_service(repository=items_price_repo)
    return InitializeItemsPriceUseCase(service=items_price_service)


# item component service and use cases
def get_init_item_components_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeItemsComponentUseCaseProtocol:
    items_component_repo = _get_item_component_repository(session=session)
    items_component_service = get_item_component_service(repository=items_component_repo)
    return InitializeItemsComponentUseCase(items_component_service)


# city trading settings
def get_init_city_trading_shop_settings_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeCityTradingShopSettingsUseCaseProtocol:
    settings_repo = _get_city_trading_shop_settings_repository(session=session)
    settings_service = get_city_trading_shop_settings_service(settings_repo)
    return InitializeCityTradingShopSettingsUseCase(service=settings_service)


# experience for level
def get_init_item_experience_for_level_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeItemExperienceForLevelUseCaseProtocol:
    experience_repo = _get_item_experience_for_level_repository(session)
    experience_service = get_item_experience_for_level_service(experience_repo)
    return InitializeItemExperienceForLevelUseCase(service=experience_service)


# building
def get_building_service(repository: BuildingRepositoryProtocol = Depends(_get_building_repository)) -> BuildingServiceProtocol:
    return BuildingService(repository=repository)


def get_init_buildings_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeBuildingsUseCaseProtocol:
    building_repo = _get_building_repository(session)
    building_service = get_building_service(building_repo)
    return InitializeBuildingsUseCase(service=building_service)
