from fastapi import APIRouter, Depends, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.crafting_license import (
    get_buy_crafting_license_use_case,
    get_get_crafting_license_status_use_case,
    get_renew_crafting_license_use_case,
)
from ..schemas import CraftingLicenseCreateSchema, CraftingLicenseReadSchema
from ..use_cases.crafting_license.buy import BuyCraftingLicenseUseCaseProtocol
from ..use_cases.crafting_license.get_status import (
    GetCraftingLicenseStatusUseCaseProtocol,
)
from ..use_cases.crafting_license.renew import RenewCraftingLicenseUseCaseProtocol

router = APIRouter()

@router.get("/crafting-license/status", response_model=CraftingLicenseReadSchema)
async def get_crafting_license_status(
    location_slug: str = Query(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCraftingLicenseStatusUseCaseProtocol = Depends(get_get_crafting_license_status_use_case)
):
    return await use_case(user.character_id, location_slug)

@router.post("/crafting-license/buy", response_model=CraftingLicenseReadSchema, status_code=201)
async def buy_crafting_license(
    data: CraftingLicenseCreateSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuyCraftingLicenseUseCaseProtocol = Depends(get_buy_crafting_license_use_case)
):
    return await use_case(user.character_id, data.location_slug)

@router.post("/crafting-license/renew", response_model=CraftingLicenseReadSchema)
async def renew_crafting_license(
    data: CraftingLicenseCreateSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: RenewCraftingLicenseUseCaseProtocol = Depends(get_renew_crafting_license_use_case)
):
    return await use_case(user.character_id, data.location_slug)
