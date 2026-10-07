import uuid

from fastapi import APIRouter, Depends, Path, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.sale import (
        get_add_item_to_sale_use_case,
        get_get_sales_history_use_case,
        get_remove_item_from_sale_use_case,
        get_update_sale_price_use_case,
)
from ..schemas import (
        LocationItemsGroupedSchema,
        SaleHistoryReadSchema,
        SaleInventoryItemCreateSchema,
        SalePriceUpdateSchema,
)
from ..use_cases.sale.add_item_to_sale import AddItemToSaleUseCaseProtocol
from ..use_cases.sale.remove_item_from_sale import RemoveItemFromSaleUseCaseProtocol
from ..use_cases.sale.update_price import UpdateSalePriceUseCaseProtocol
from ..use_cases.sale_history.get_sales_history import GetSalesHistoryUseCaseProtocol

router = APIRouter()

@router.post('/sale/inventory/{inventory_item_id}', response_model=LocationItemsGroupedSchema, status_code=201)
async def add_item_to_sale(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    data: SaleInventoryItemCreateSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AddItemToSaleUseCaseProtocol = Depends(get_add_item_to_sale_use_case)
) -> LocationItemsGroupedSchema:
        return await use_case(inventory_item_id, data.price, user, data.amount)

@router.delete('/sale/inventory/{inventory_item_id}', response_model=LocationItemsGroupedSchema, status_code=200)
async def remove_item_from_sale(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    amount: int = Query(None, ge=1, description="Сколько забрать (по умолчанию — все)"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: RemoveItemFromSaleUseCaseProtocol = Depends(get_remove_item_from_sale_use_case)
) -> LocationItemsGroupedSchema:
    return await use_case(inventory_item_id, user, amount)

@router.patch('/sale/inventory/{inventory_item_id}/price', response_model=LocationItemsGroupedSchema)
async def update_sale_price(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    data: SalePriceUpdateSchema = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateSalePriceUseCaseProtocol = Depends(get_update_sale_price_use_case),
) -> LocationItemsGroupedSchema:
    return await use_case(inventory_item_id, data.price, user)


@router.get('/city-shop/sales-history', response_model=list[SaleHistoryReadSchema])
async def get_sales_history(
    limit: int = Query(30, ge=1, le=100),
    location_slug: str = Query(None, min_length=1, max_length=128),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetSalesHistoryUseCaseProtocol = Depends(get_get_sales_history_use_case),
) -> list[SaleHistoryReadSchema]:
    return await use_case(user, limit, location_slug)
