import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from ....core.depends import get_user_token_payload
from ..deps.purchase import get_purchase_item_use_case
from ..schemas import InventoryItemAmountSchema
from ..use_cases.purchase.purchase_item import PurchaseItemUseCaseProtocol

router = APIRouter()


@router.post('/purchase/inventory/{inventory_item_id}', response_model=StatusOkSchema, status_code=200)
async def purchase_item(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item to purchase"),
    data: InventoryItemAmountSchema | None = None,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: PurchaseItemUseCaseProtocol = Depends(get_purchase_item_use_case)
) -> StatusOkSchema:
    amount = data.amount if data else None
    return await use_case(inventory_item_id, user, amount)
