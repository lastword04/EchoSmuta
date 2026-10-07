import uuid

from fastapi import APIRouter, Depends, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deals.enums import DealStatus
from ..deals.schemas import (
    DealCreateSchema,
    DealCurrencyOfferUpdateSchema,
    DealDetailSchema,
    DealInventoryItemOfferCreateSchema,
    DealItemReadSchema,
    DealListSchema,
    DealOfferReadSchema,
    DealReadSchema,
    DealResourceOfferUpdateSchema,
    NearbyPartnerSchema,
    TradeLicenseStatusSchema,
)
from ..deals.use_cases import (
    AcceptDealUseCaseProtocol,
    AddDealInventoryItemUseCaseProtocol,
    AddDealResourceUseCaseProtocol,
    CancelDealUseCaseProtocol,
    ConfirmDealUseCaseProtocol,
    CreateDealUseCaseProtocol,
    GetDealUseCaseProtocol,
    ListDealsUseCaseProtocol,
    ListNearbyPartnersUseCaseProtocol,
    RemoveDealItemUseCaseProtocol,
    SetDealDucatsUseCaseProtocol,
    SetDealGoldUseCaseProtocol,
    TradeLicenseUseCase,
)
from ..deps.deals import (
    get_accept_deal_use_case,
    get_add_deal_inventory_item_use_case,
    get_add_deal_resource_use_case,
    get_cancel_deal_use_case,
    get_confirm_deal_use_case,
    get_create_deal_use_case,
    get_deal_use_case,
    get_list_deals_use_case,
    get_list_nearby_partners_use_case,
    get_remove_deal_item_use_case,
    get_set_deal_ducats_use_case,
    get_set_deal_gold_use_case,
    get_trade_license_use_case,
)

router = APIRouter()


@router.get('/deals', response_model=DealListSchema)
async def list_deals(
    status: list[DealStatus] | None = Query(None),
    limit: int = Query(20, gt=0, le=100),
    offset: int = Query(0, ge=0),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ListDealsUseCaseProtocol = Depends(get_list_deals_use_case),
) -> DealListSchema:
    return await use_case(user, status, limit, offset)


@router.post('/deals', response_model=DealReadSchema, status_code=201)
async def create_deal(
    data: DealCreateSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateDealUseCaseProtocol = Depends(get_create_deal_use_case),
) -> DealReadSchema:
    return await use_case(user, data)


@router.get('/deals/partners/nearby', response_model=list[NearbyPartnerSchema])
async def list_nearby_deal_partners(
    location_slug: str = Query(..., min_length=1, max_length=128),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ListNearbyPartnersUseCaseProtocol = Depends(get_list_nearby_partners_use_case),
) -> list[NearbyPartnerSchema]:
    return await use_case(user, location_slug)


@router.get('/deals/{deal_id}', response_model=DealDetailSchema)
async def get_deal(
    deal_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetDealUseCaseProtocol = Depends(get_deal_use_case),
) -> DealDetailSchema:
    return await use_case(deal_id, user)


@router.post('/deals/{deal_id}/accept', response_model=DealReadSchema)
async def accept_deal(
    deal_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AcceptDealUseCaseProtocol = Depends(get_accept_deal_use_case),
) -> DealReadSchema:
    return await use_case(deal_id, user)


@router.post('/deals/{deal_id}/cancel', response_model=DealReadSchema)
async def cancel_deal(
    deal_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CancelDealUseCaseProtocol = Depends(get_cancel_deal_use_case),
) -> DealReadSchema:
    return await use_case(deal_id, user.character_id)


@router.post('/deals/{deal_id}/confirm', response_model=DealReadSchema)
async def confirm_deal(deal_id: uuid.UUID, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: ConfirmDealUseCaseProtocol = Depends(get_confirm_deal_use_case)) -> DealReadSchema:
    return await use_case(deal_id, user)


@router.get('/trade-license/status', response_model=TradeLicenseStatusSchema)
async def get_trade_license_status(user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: TradeLicenseUseCase = Depends(get_trade_license_use_case)) -> TradeLicenseStatusSchema:
    return await use_case.status(user.character_id)


@router.post('/trade-license/renew', response_model=TradeLicenseStatusSchema)
async def renew_trade_license(user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: TradeLicenseUseCase = Depends(get_trade_license_use_case)) -> TradeLicenseStatusSchema:
    return await use_case.renew(user.character_id)


@router.put('/deals/{deal_id}/offer/ducats', response_model=DealOfferReadSchema)
async def set_deal_ducats(deal_id: uuid.UUID, data: DealCurrencyOfferUpdateSchema, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: SetDealDucatsUseCaseProtocol = Depends(get_set_deal_ducats_use_case)) -> DealOfferReadSchema:
    return await use_case(deal_id, user, data)


@router.put('/deals/{deal_id}/offer/gold', response_model=DealOfferReadSchema)
async def set_deal_gold(deal_id: uuid.UUID, data: DealCurrencyOfferUpdateSchema, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: SetDealGoldUseCaseProtocol = Depends(get_set_deal_gold_use_case)) -> DealOfferReadSchema:
    return await use_case(deal_id, user, data)


@router.put('/deals/{deal_id}/offer/resources/{resource_slug}', response_model=DealItemReadSchema)
async def add_deal_resource(deal_id: uuid.UUID, resource_slug: str, data: DealResourceOfferUpdateSchema, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: AddDealResourceUseCaseProtocol = Depends(get_add_deal_resource_use_case)) -> DealItemReadSchema:
    return await use_case(deal_id, resource_slug, user, data)


@router.delete('/deals/{deal_id}/offer/resources/{resource_slug}', status_code=204)
async def remove_deal_resource(deal_id: uuid.UUID, resource_slug: str, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: RemoveDealItemUseCaseProtocol = Depends(get_remove_deal_item_use_case)) -> None:
    await use_case.remove_resource(deal_id, resource_slug, user)


@router.post('/deals/{deal_id}/offer/items', response_model=DealItemReadSchema, status_code=201)
async def add_deal_inventory_item(deal_id: uuid.UUID, data: DealInventoryItemOfferCreateSchema, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: AddDealInventoryItemUseCaseProtocol = Depends(get_add_deal_inventory_item_use_case)) -> DealItemReadSchema:
    return await use_case(deal_id, user, data)


@router.delete('/deals/{deal_id}/offer/items/{deal_item_id}', status_code=204)
async def remove_deal_item(deal_id: uuid.UUID, deal_item_id: uuid.UUID, user: UserTokenDataReadSchema = Depends(get_user_token_payload), use_case: RemoveDealItemUseCaseProtocol = Depends(get_remove_deal_item_use_case)) -> None:
    await use_case(deal_id, deal_item_id, user)

