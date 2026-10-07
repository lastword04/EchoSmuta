import uuid
from fastapi import APIRouter, Depends, Path, Query
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .schemas import (
    SlotRequestSchema, SlotReadSchema, SlotPaginationResultSchema,
    ExchangeSettingsReadSchema, BuySlotResponse
)  
from .enums import Currency
from .use_cases.slots.create import CreateSlotUseCaseProtocol
from .use_cases.slots.delete import DeleteSlotUseCaseProtocol
from .use_cases.slots.paginate import GetPaginatedSlotsUseCaseProtocol
from .use_cases.slots.buy import BuySlotUseCaseProtocol
from .use_cases.exchanges_settings.get import GetExchangeSettingsUseCaseProtocol
from .depends import (
   get_create_slot_use_case,
   get_delete_slot_use_case,
   get_get_paginated_slots_use_case,
   get_buy_slot_use_case,
   get_get_all_exchange_settings_use_case
)

router = APIRouter(prefix='/api/slots', tags=['Slots'])

@router.post('/', response_model=SlotReadSchema)
async def create_slot(
    data: SlotRequestSchema,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateSlotUseCaseProtocol = Depends(get_create_slot_use_case)
) -> SlotReadSchema:
    return await use_case(data, token)

@router.post('/{slot_id}/buy', response_model=BuySlotResponse)
async def buy_slot(
    slot_id: uuid.UUID = Path(..., description="ID of the slot to buy"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuySlotUseCaseProtocol = Depends(get_buy_slot_use_case)
) -> BuySlotResponse:
    return await use_case(slot_id, token)

@router.get('/', response_model=SlotPaginationResultSchema)
async def get_paginated_slots(
    limit: int = Query(10, gt=0, le=100, description="Number of slots to return"),
    offset: int = Query(0, ge=0, description="Number of slots to skip"),
    buy_for: Currency = Query(..., description="Currency to buy slots"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetPaginatedSlotsUseCaseProtocol = Depends(get_get_paginated_slots_use_case)
) -> SlotPaginationResultSchema:
    return await use_case(limit, offset, buy_for, token)

@router.get('/settings', response_model=ExchangeSettingsReadSchema)
async def get_exchange_settings(
    use_case: GetExchangeSettingsUseCaseProtocol = Depends(get_get_all_exchange_settings_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
) -> ExchangeSettingsReadSchema:
    return await use_case()

@router.delete('/{slot_id}', status_code=204)
async def delete_slot(
    slot_id: uuid.UUID = Path(..., description="ID of the slot to delete"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DeleteSlotUseCaseProtocol = Depends(get_delete_slot_use_case)
) -> None:
    await use_case(slot_id, token)