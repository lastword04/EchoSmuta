import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from ....core.depends import get_user_token_payload
from ..deps.crafting import (
    get_continue_item_crafting_use_case,
    get_create_new_item_crafting_use_case,
    get_get_character_creating_items_use_case,
    get_get_crafting_status_use_case,
    get_get_items_creating_action_use_case,
    get_items_creating_action_service,
)
from ..schemas import (
    CharacterRecipeWithStockSchema,
    ContinueItemCraftingRequestSchema,
    CreateNewItemCraftingRequestSchema,
    ItemsCreatingActionReadSchema,
    ItemsCreatingActionResponseSchema,
)
from ..services.crafting.items_creating_actions import (
    ItemsCreatingActionServiceProtocol,
)
from ..use_cases.crafting.continue_item_crafting import (
    ContinueItemCraftingUseCaseProtocol,
)
from ..use_cases.crafting.create_new_item_crafting import (
    CreateNewItemCraftingUseCaseProtocol,
)
from ..use_cases.crafting.get_character_creating_items import (
    GetCharacterCreatingItemsUseCaseProtocol,
)
from ..use_cases.crafting.get_crafting_status import GetCraftingStatusUseCaseProtocol
from ..use_cases.crafting.get_items_creating_action import (
    GetItemsCreatingActionUseCaseProtocol,
)

router = APIRouter()

@router.get('/creating', response_model=list[CharacterRecipeWithStockSchema])
async def get_character_creating_items(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharacterCreatingItemsUseCaseProtocol = Depends(get_get_character_creating_items_use_case)
) -> list[CharacterRecipeWithStockSchema]:
    return await use_case(user)

@router.post('/crafting/{recipe_id}/new', response_model=ItemsCreatingActionReadSchema, status_code=201)
async def create_new_item_crafting(
    recipe_id: uuid.UUID = Path(..., description="ID of the recipe"),
    data: CreateNewItemCraftingRequestSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateNewItemCraftingUseCaseProtocol = Depends(get_create_new_item_crafting_use_case)
) -> ItemsCreatingActionReadSchema:
    """Start crafting a new item (craft_stage=0)"""
    from shared.schemas.captcha import CaptchaVerificationRequest
    
    captcha = CaptchaVerificationRequest(
        captcha_id=data.captcha_id,
        user_input=data.user_input
    )
    
    return await use_case(
        character_id=user.character_id,
        recipe_id=recipe_id,
        captcha=captcha
    )


@router.post('/crafting/{start_creating_id}/continue', response_model=ItemsCreatingActionReadSchema, status_code=201)
async def continue_item_crafting(
    start_creating_id: uuid.UUID = Path(..., description="ID of the CharacterStartCreatingItem"),
    data: ContinueItemCraftingRequestSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ContinueItemCraftingUseCaseProtocol = Depends(get_continue_item_crafting_use_case)
) -> ItemsCreatingActionReadSchema:
    """Continue crafting an existing item (craft_stage > 0)"""
    from shared.schemas.captcha import CaptchaVerificationRequest
    
    captcha = CaptchaVerificationRequest(
        captcha_id=data.captcha_id,
        user_input=data.user_input
    )
    
    return await use_case(
        character_id=user.character_id,
        start_creating_id=start_creating_id,
        captcha=captcha
    )

@router.get('/crafting/status', response_model=ItemsCreatingActionResponseSchema)
async def get_crafting_status(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCraftingStatusUseCaseProtocol = Depends(get_get_crafting_status_use_case)
) -> ItemsCreatingActionResponseSchema:
    """Get current crafting status - returns IN_PROGRESS action or status DONE if no active crafting"""
    return await use_case(user.character_id)

@router.post('/crafting/cancel-expired', response_model=StatusOkSchema)
async def cancel_expired_crafting(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    service: ItemsCreatingActionServiceProtocol = Depends(get_items_creating_action_service),
) -> StatusOkSchema:
    """Отменить зависшие крафты, у которых время давно вышло"""
    await service.cancel_expired_actions(user.character_id)
    return StatusOkSchema(status='ok')


@router.get('/crafting/action/{id}', response_model=ItemsCreatingActionReadSchema)
async def get_items_creating_action(
    id: uuid.UUID = Path(..., description="ID of the ItemsCreatingAction"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetItemsCreatingActionUseCaseProtocol = Depends(get_get_items_creating_action_use_case)
) -> ItemsCreatingActionReadSchema:
    """Get a specific ItemsCreatingAction by id for the current character"""
    return await use_case(id, user.character_id)
