import uuid
from fastapi import APIRouter, Depends, Path, Query
from typing import Optional
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.category import BaseCategoryStatsSchema
from ...core.depends import get_user_token_payload, get_service_token_payload
from .schemas import (
   CategoryCreateSchema, CategoryReadSchema,
   CategoryWithCharacterCountSchema, CategoryWithCharactersReadSchema,
   CategoryUpdateCheckbox
)
from .use_cases.categories.create import CreateCategoriesUseCaseProtocol
from .use_cases.categories.delete import DeleteCategoriesUseCaseProtocol
from .use_cases.categories.get_my import GetMyCategoriesUseCaseProtocol
from .use_cases.categories.get_my_with_counts import GetMyWithCountsCategoriesUseCaseProtocol
from .use_cases.categories.update_checkbox import UpdateCategoriesUseCaseProtocol
from .use_cases.categories_characters.add_character_to_category import AddCharacterToCategoryUseCaseProtocol
from .use_cases.categories_characters.get_by_category import GetByCategoryUseCaseProtocol
from .use_cases.categories_characters.delete_character_from_category import DeleteCharacterFromCategoryUseCaseProtocol
from .use_cases.categories.calculate_stats_base_category import GetCategoriesStatsUseCaseProtocol
from .depends import (
    get_create_category_use_case,
    get_delete_category_use_case,
    get_get_my_categories_use_case,
    get_get_my_with_counts_categories_use_case,
    get_add_character_to_category,
    get_get_by_category,
    get_delete_character_from_category_use_case,
    get_update_checkbox_for_categories_use_case,
    get_categories_stats_use_case
)

router = APIRouter(prefix='/api/categories', tags=['Categories'])

@router.post('/', response_model=list[CategoryWithCharacterCountSchema], status_code=201)
async def create_category(
    category: CategoryCreateSchema,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateCategoriesUseCaseProtocol = Depends(get_create_category_use_case)
) -> CategoryReadSchema:
    return await use_case(
        category, token
    )

@router.post('/{category_id}/characters/{character_name}', response_model=CategoryWithCharactersReadSchema, status_code=201)
async def add_character_to_category(
    category_id: uuid.UUID = Path(..., description="Id of category"),
    character_name: str = Path(..., description="Id of character"),
    is_online: Optional[bool] = Query(None, description="Search only online or offline characters"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AddCharacterToCategoryUseCaseProtocol = Depends(get_add_character_to_category)
) -> CategoryWithCharactersReadSchema:
    return await use_case(category_id, character_name, token, is_online)

@router.delete('/{category_id}/characters/{character_id}', response_model=CategoryWithCharactersReadSchema, status_code=201)
async def delete_character_from_category(
    category_id: uuid.UUID = Path(..., description="Id of category"),
    character_id: uuid.UUID = Path(..., description="Id of character"),
    is_online: Optional[bool] = Query(None, description="Search only online or offline characters"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DeleteCharacterFromCategoryUseCaseProtocol = Depends(get_delete_character_from_category_use_case)
) -> CategoryWithCharactersReadSchema:
    return await use_case(category_id, character_id, token, is_online)


@router.delete('/{category_id}', response_model=None, status_code=204)
async def delete_category(
    category_id = Path(..., description="Id of category"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DeleteCategoriesUseCaseProtocol = Depends(get_delete_category_use_case)
) -> None:
    await use_case(category_id, token)

    return None

@router.put('/{category_id}', response_model=list[CategoryWithCharacterCountSchema])
async def update_category_checkbox(
    checkboxes: CategoryUpdateCheckbox,
    category_id = Path(..., description="Id of category"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateCategoriesUseCaseProtocol = Depends(get_update_checkbox_for_categories_use_case)
) -> list[CategoryWithCharacterCountSchema]:
    return await use_case(category_id, token, checkboxes)

@router.get('/', response_model=list[CategoryReadSchema])
async def get_my_categories(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyCategoriesUseCaseProtocol = Depends(get_get_my_categories_use_case)
) -> list[CategoryReadSchema]:
    return await use_case(token)

@router.get('/detail', response_model=list[CategoryWithCharacterCountSchema])
async def get_my_categories_with_counts(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyWithCountsCategoriesUseCaseProtocol = Depends(get_get_my_with_counts_categories_use_case)
) -> list[CategoryWithCharacterCountSchema]:
    return await use_case(token)

@router.get('/characters/{character_id}', response_model=BaseCategoryStatsSchema)
async def get_category_stats(
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: GetCategoriesStatsUseCaseProtocol = Depends(get_categories_stats_use_case)
) -> BaseCategoryStatsSchema:
    return await use_case(character_id)

@router.get('/{category_id}', response_model=CategoryWithCharactersReadSchema, status_code=201)
async def get_by_category(
    category_id: uuid.UUID = Path(..., description="Id of category"),
    is_online: Optional[bool] = Query(None, description="Search only online or offline characters"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetByCategoryUseCaseProtocol = Depends(get_get_by_category)
) -> CategoryWithCharactersReadSchema:
    return await use_case(category_id, token, is_online)

