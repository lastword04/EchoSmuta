from fastapi import APIRouter, Depends

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.settings import get_get_ct_shop_buy_settings_use_case
from ..schemas import CityTradingShopBuySettingsReadSchema
from ..use_cases.settings.get_settings_trading_shop_buy_by_loc_slug import (
    GetCTShopBuySettingsUseCaseProtocol,
)

router = APIRouter()


@router.get('/city-shop/settings', response_model=CityTradingShopBuySettingsReadSchema)
async def get_city_shop_buy_settings_for_character(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCTShopBuySettingsUseCaseProtocol = Depends(get_get_ct_shop_buy_settings_use_case)
) -> CityTradingShopBuySettingsReadSchema:
    return await use_case(user)
