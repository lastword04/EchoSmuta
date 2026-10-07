"""Провайдеры crafting-домена: крафт предметов, Items Creating Actions,
wiring crafting event handler.

Фабрики (get_cancel_crafting_actions_factory, get_crafting_handler) не
используют Depends: они собирают зависимости вручную.
"""
from fastapi import Depends

from ....core.db import AsyncSession
from ....settings import Settings, get_settings
from ...resources.depends import (
    get_character_resource_service,
    get_redis_publisher,
)
from ...resources.events.publisher import RedisPublisherProtocol
from ...resources.services.character_resource import CharacterResourceServiceProtocol
from ..adapters.captcha import CaptchaServiceClientProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..events.handlers.crafting import (
    CraftingEventHandler,
    CraftingEventHandlerProtocol,
)
from ..events.items import ItemEventsProtocol
from ..repositories.building.building import BuildingRepositoryProtocol
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.crafting.character_start_creating_item import (
    CharacterStartCreatingItemRepositoryProtocol,
)
from ..repositories.crafting.items_creating_action import (
    ItemsCreatingActionRepository,
    ItemsCreatingActionRepositoryProtocol,
)
from ..repositories.recipes.character_recipes import CharacterRecipesRepositoryProtocol
from ..repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepositoryProtocol,
)
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.crafting.character_start_creating_item import (
    CharacterStartCreatingItemService,
    CharacterStartCreatingItemServiceProtocol,
)
from ..services.crafting.items_creating_actions import (
    CancelItemsCreatingProcessService,
    CancelItemsCreatingProcessServiceProtocol,
    CreateItemsCreatingActionService,
    CreateItemsCreatingActionServiceProtocol,
    ItemsCreatingActionService,
    ItemsCreatingActionServiceProtocol,
    ProcessItemsCreatingActionService,
    ProcessItemsCreatingActionServiceProtocol,
    ValidateCreateItemActionService,
    ValidateCreateItemActionServiceProtocol,
)
from ..services.crafting.processors import CraftingResultProcessor
from ..services.crafting.validators import CraftingValidator
from ..services.crafting_license.crafting_license import CraftingLicenseServiceProtocol
from ..services.items.experience_for_level import ItemExperienceForLevelServiceProtocol
from ..services.items.items import ItemServiceProtocol
from ..services.items.items_component import ItemComponentServiceProtocol
from ..services.recipes.character_recipes import CharacterRecipesServiceProtocol
from ..use_cases.crafting.continue_item_crafting import (
    ContinueItemCraftingUseCase,
    ContinueItemCraftingUseCaseProtocol,
)
from ..use_cases.crafting.create_new_item_crafting import (
    CreateNewItemCraftingUseCase,
    CreateNewItemCraftingUseCaseProtocol,
)
from ..use_cases.crafting.get_character_creating_items import (
    GetCharacterCreatingItemsUseCase,
    GetCharacterCreatingItemsUseCaseProtocol,
)
from ..use_cases.crafting.get_crafting_status import (
    GetCraftingStatusUseCase,
    GetCraftingStatusUseCaseProtocol,
)
from ..use_cases.crafting.get_items_creating_action import (
    GetItemsCreatingActionUseCase,
    GetItemsCreatingActionUseCaseProtocol,
)
from .adapters import (
    get_captcha_service_client,
    get_character_service_client,
    get_item_template_service,
)
from .crafting_license import get_crafting_license_service
from .events import get_items_events
from .items import (
    get_item_component_service,
    get_item_experience_for_level_service,
    get_item_service,
)
from .recipes import get_character_recipes_service
from .repositories import (
    _get_building_repository,
    _get_character_city_trade_stats_repository,
    _get_character_item_repository,
    _get_character_recipes_repository,
    _get_character_start_creating_item_repository,
    _get_city_trading_shop_character_repository,
    _get_items_creating_action_repository,
)


# character start creating item
def get_character_start_creating_item_service(
    repository: CharacterStartCreatingItemRepositoryProtocol = Depends(_get_character_start_creating_item_repository)
) -> CharacterStartCreatingItemServiceProtocol:
    return CharacterStartCreatingItemService(repository=repository)


def get_get_character_creating_items_use_case(
    crafting_service: CharacterStartCreatingItemServiceProtocol = Depends(get_character_start_creating_item_service),
    recipes_service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> GetCharacterCreatingItemsUseCaseProtocol:
    return GetCharacterCreatingItemsUseCase(
        crafting_service=crafting_service,
        recipes_service=recipes_service
    )


# Items Creating Actions
def get_items_creating_action_service(
    repository: ItemsCreatingActionRepositoryProtocol = Depends(_get_items_creating_action_repository)
) -> ItemsCreatingActionServiceProtocol:
    return ItemsCreatingActionService(repository=repository)


def get_get_items_creating_action_use_case(
    service: ItemsCreatingActionServiceProtocol = Depends(get_items_creating_action_service)
) -> GetItemsCreatingActionUseCaseProtocol:
    return GetItemsCreatingActionUseCase(service=service)


def get_get_crafting_status_use_case(
    service: ItemsCreatingActionServiceProtocol = Depends(get_items_creating_action_service)
) -> GetCraftingStatusUseCaseProtocol:
    return GetCraftingStatusUseCase(service=service)


def get_create_items_creating_action_service(
    repository: ItemsCreatingActionRepositoryProtocol = Depends(_get_items_creating_action_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    building_repository: BuildingRepositoryProtocol = Depends(_get_building_repository),
    item_service: ItemServiceProtocol = Depends(get_item_service),
    character_resource_service: CharacterResourceServiceProtocol = Depends(get_character_resource_service),
    item_component_service: ItemComponentServiceProtocol = Depends(get_item_component_service),
    city_trading_shop_repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    character_recipes_repository: CharacterRecipesRepositoryProtocol = Depends(_get_character_recipes_repository),
    character_start_creating_repository: CharacterStartCreatingItemRepositoryProtocol = Depends(_get_character_start_creating_item_repository),
    settings: Settings = Depends(get_settings),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    crafting_license_service: CraftingLicenseServiceProtocol = Depends(get_crafting_license_service),
    captcha_adapter: CaptchaServiceClientProtocol = Depends(get_captcha_service_client),
) -> CreateItemsCreatingActionServiceProtocol:
    # Валидация запуска крафта вынесена в CraftingValidator
    validator = CraftingValidator(
        building_repository=building_repository,
        city_trading_shop_repository=city_trading_shop_repository,
        item_component_service=item_component_service,
        character_resource_service=character_resource_service,
        crafting_license_service=crafting_license_service,
        min_valid_level=settings.items_creating.min_valid_character_level,
        max_valid_tiredness=settings.items_creating.max_valid_character_tiredness,
    )
    return CreateItemsCreatingActionService(
        repository=repository,
        character_service=character_service,
        building_repository=building_repository,
        item_service=item_service,
        character_resource_service=character_resource_service,
        item_component_service=item_component_service,
        city_trading_shop_repository=city_trading_shop_repository,
        character_recipes_repository=character_recipes_repository,
        character_start_creating_repository=character_start_creating_repository,
        template_service=template_service,
        items_events=items_events,
        cooldown_seconds=settings.items_creating.cooldown_seconds,
        crafting_license_service=crafting_license_service,
        captcha_adapter=captcha_adapter,
        validator=validator
    )


def get_process_items_creating_action_service(
    repository: ItemsCreatingActionRepositoryProtocol = Depends(_get_items_creating_action_repository),
    character_start_creating_repository: CharacterStartCreatingItemRepositoryProtocol = Depends(_get_character_start_creating_item_repository),
    character_item_repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    item_service: ItemServiceProtocol = Depends(get_item_service),
    item_component_service: ItemComponentServiceProtocol = Depends(get_item_component_service),
    character_resource_service: CharacterResourceServiceProtocol = Depends(get_character_resource_service),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    character_city_trade_stats_repository: CharacterCityTradeStatsRepositoryProtocol = Depends(_get_character_city_trade_stats_repository),
    item_experience_for_level_service: ItemExperienceForLevelServiceProtocol = Depends(get_item_experience_for_level_service),
    settings: Settings = Depends(get_settings),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> ProcessItemsCreatingActionServiceProtocol:
    # Обработка результата стадии крафта вынесена в CraftingResultProcessor
    processor = CraftingResultProcessor(
        repository=repository,
        character_start_creating_repository=character_start_creating_repository,
        character_item_repository=character_item_repository,
        character_resource_service=character_resource_service,
        character_service=character_service,
        character_city_trade_stats_repository=character_city_trade_stats_repository,
        item_experience_for_level_service=item_experience_for_level_service,
        template_service=template_service,
        items_events=items_events,
        redis_publisher=redis_publisher,
        change_tiredness=settings.items_creating.change_tiredness,
        chance_lose_resource=settings.items_creating.chance_lose_resource,
    )
    return ProcessItemsCreatingActionService(
        repository=repository,
        character_start_creating_repository=character_start_creating_repository,
        character_item_repository=character_item_repository,
        item_service=item_service,
        item_component_service=item_component_service,
        character_resource_service=character_resource_service,
        character_service=character_service,
        character_city_trade_stats_repository=character_city_trade_stats_repository,
        item_experience_for_level_service=item_experience_for_level_service,
        template_service=template_service,
        items_events=items_events,
        redis_publisher=redis_publisher,
        change_tiredness=settings.items_creating.change_tiredness,
        chance_lose_resource=settings.items_creating.chance_lose_resource,
        processor=processor
    )


def get_validate_create_item_action_service(
    creating_checker: ItemsCreatingActionServiceProtocol = Depends(get_items_creating_action_service),
    creating_creator: CreateItemsCreatingActionServiceProtocol = Depends(get_create_items_creating_action_service)
) -> ValidateCreateItemActionServiceProtocol:
    return ValidateCreateItemActionService(
        creating_checker=creating_checker,
        creating_creator=creating_creator
    )


# Use Cases
def get_create_new_item_crafting_use_case(
    service: ValidateCreateItemActionServiceProtocol = Depends(get_validate_create_item_action_service)
) -> CreateNewItemCraftingUseCaseProtocol:
    return CreateNewItemCraftingUseCase(service=service)


def get_continue_item_crafting_use_case(
    service: ValidateCreateItemActionServiceProtocol = Depends(get_validate_create_item_action_service)
) -> ContinueItemCraftingUseCaseProtocol:
    return ContinueItemCraftingUseCase(service=service)


# Crafting events (аналог mining handler)
def get_cancel_crafting_actions_factory():
    def factory(session: AsyncSession) -> CancelItemsCreatingProcessServiceProtocol:
        return CancelItemsCreatingProcessService(
            repository=ItemsCreatingActionRepository(session=session)
        )
    return factory

def get_crafting_handler(
    redis_subscriber,
    cancel_crafting_service_factory,
) -> CraftingEventHandlerProtocol:
    return CraftingEventHandler(
        subscriber=redis_subscriber,
        crafting_service_factory=cancel_crafting_service_factory,
    )
