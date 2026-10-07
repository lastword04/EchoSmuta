from fastapi import APIRouter, Depends, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.recipes import (
    get_buy_recipe_use_case,
    get_get_all_recipes_use_case,
    get_get_character_recipes_with_details_use_case,
    get_get_character_recipes_with_stock_use_case,
)
from ..schemas import (
    CharacterRecipeCreateSchema,
    CharacterRecipeReadSchema,
    CharacterRecipeWithDetailsSchema,
    CharacterRecipeWithStockSchema,
    ResourceItemWithComponentsReadSchema,
)
from ..use_cases.recipes.buy_recipe import BuyRecipeUseCaseProtocol
from ..use_cases.recipes.get_all_recipes import GetAllRecipesUseCaseProtocol
from ..use_cases.recipes.get_character_recipes_with_details import (
    GetCharacterRecipesWithDetailsUseCaseProtocol,
)
from ..use_cases.recipes.get_character_recipes_with_stock import (
    GetCharacterRecipesWithStockUseCaseProtocol,
)

router = APIRouter()


@router.get('/recipes', response_model=list[ResourceItemWithComponentsReadSchema])
async def get_all_recipes_for_character(
    quantity: int = Query(..., gt=0, le=100),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetAllRecipesUseCaseProtocol = Depends(get_get_all_recipes_use_case)
) -> list[ResourceItemWithComponentsReadSchema]:
    return await use_case(user, quantity)


@router.post('/recipes', response_model=CharacterRecipeReadSchema, status_code=201)
async def buy_recipe(
    data: CharacterRecipeCreateSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuyRecipeUseCaseProtocol = Depends(get_buy_recipe_use_case)
) -> CharacterRecipeReadSchema:
    return await use_case(user, data)

@router.get('/recipes/me', response_model=list[CharacterRecipeWithDetailsSchema])
async def get_character_recipes_with_details(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharacterRecipesWithDetailsUseCaseProtocol = Depends(get_get_character_recipes_with_details_use_case)
) -> list[CharacterRecipeWithDetailsSchema]:
    return await use_case(user)

@router.get('/recipes/me/stock', response_model=list[CharacterRecipeWithStockSchema])
async def get_character_recipes_with_stock(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    # location_slug городской лавки (например, 1.21.furniture-shop): фильтр стока по ней,
    # а не по текущей локации персонажа. Без параметра — прежнее поведение.
    location_slug: str | None = Query(None),
    use_case: GetCharacterRecipesWithStockUseCaseProtocol = Depends(get_get_character_recipes_with_stock_use_case)
) -> list[CharacterRecipeWithStockSchema]:
    return await use_case(user, location_slug)
