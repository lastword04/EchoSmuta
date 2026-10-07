"""Провайдеры рецептов персонажа (recipes-домен)."""
from fastapi import Depends

from ....core.db import AsyncSession, get_async_session
from ..adapters.characters import CharacterServiceClientProtocol
from ..events.items import ItemEventsProtocol
from ..repositories.building.building import BuildingRepositoryProtocol
from ..repositories.items.items import ItemRepositoryProtocol
from ..repositories.items.items_component import ItemComponentRepositoryProtocol
from ..repositories.recipes.character_recipes import CharacterRecipesRepositoryProtocol
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.recipes.character_recipes import (
    CharacterRecipesService,
    CharacterRecipesServiceProtocol,
)
from ..use_cases.recipes.buy_recipe import BuyRecipeUseCase, BuyRecipeUseCaseProtocol
from ..use_cases.recipes.get_all_recipes import (
    GetAllRecipesUseCase,
    GetAllRecipesUseCaseProtocol,
)
from ..use_cases.recipes.get_character_recipes import (
    GetCharacterRecipesUseCase,
    GetCharacterRecipesUseCaseProtocol,
)
from ..use_cases.recipes.get_character_recipes_with_details import (
    GetCharacterRecipesWithDetailsUseCase,
    GetCharacterRecipesWithDetailsUseCaseProtocol,
)
from ..use_cases.recipes.get_character_recipes_with_stock import (
    GetCharacterRecipesWithStockUseCase,
    GetCharacterRecipesWithStockUseCaseProtocol,
)
from .adapters import get_character_service_client, get_item_template_service
from .events import get_items_events
from .repositories import (
    _get_building_repository,
    _get_character_recipes_repository,
    _get_item_component_repository,
    _get_item_repository,
)


# recipes
def get_character_recipes_service(
    repository: CharacterRecipesRepositoryProtocol = Depends(_get_character_recipes_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    item_repository: ItemRepositoryProtocol = Depends(_get_item_repository),
    component_repository: ItemComponentRepositoryProtocol = Depends(_get_item_component_repository),
    session: AsyncSession = Depends(get_async_session),
    building_repository: BuildingRepositoryProtocol = Depends(_get_building_repository),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
) -> CharacterRecipesServiceProtocol:
    return CharacterRecipesService(
        repository=repository,
        character_client=character_client,
        item_repository=item_repository,
        component_repository=component_repository,
        session=session,
        building_repository=building_repository,
        template_service=template_service,
        items_events=items_events,
    )

def get_get_all_recipes_use_case(
    service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> GetAllRecipesUseCaseProtocol:
    return GetAllRecipesUseCase(service=service)

def get_get_character_recipes_use_case(
    service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> GetCharacterRecipesUseCaseProtocol:
    return GetCharacterRecipesUseCase(service=service)

def get_buy_recipe_use_case(
    service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> BuyRecipeUseCaseProtocol:
    return BuyRecipeUseCase(service=service)

def get_get_character_recipes_with_details_use_case(
    service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> GetCharacterRecipesWithDetailsUseCaseProtocol:
    return GetCharacterRecipesWithDetailsUseCase(service=service)

def get_get_character_recipes_with_stock_use_case(
    service: CharacterRecipesServiceProtocol = Depends(get_character_recipes_service)
) -> GetCharacterRecipesWithStockUseCaseProtocol:
    return GetCharacterRecipesWithStockUseCase(service=service)
