import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.shop import (
    get_list_item_to_shop_use_case,
    get_withdraw_item_from_shop_use_case,
)
from ..schemas import InventoryItemAmountSchema, LocationItemsGroupedSchema
from ..use_cases.shop.list_item_to_shop import ListItemToShopUseCaseProtocol
from ..use_cases.shop.withdraw_item_from_shop import WithdrawItemFromShopUseCaseProtocol

router = APIRouter()

@router.post('/shops/inventory/{item_id}/list', response_model=LocationItemsGroupedSchema, status_code=200)
async def list_item_to_shop(
    item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    data: InventoryItemAmountSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ListItemToShopUseCaseProtocol = Depends(get_list_item_to_shop_use_case)
) -> LocationItemsGroupedSchema:
    return await use_case(item_id, user, data.amount)

@router.post('/shops/inventory/{item_id}/withdraw', response_model=LocationItemsGroupedSchema, status_code=200)
async def withdraw_item_from_shop(
    item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    data: InventoryItemAmountSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: WithdrawItemFromShopUseCaseProtocol = Depends(get_withdraw_item_from_shop_use_case)
) -> LocationItemsGroupedSchema:
    return await use_case(item_id, user, data.amount)
