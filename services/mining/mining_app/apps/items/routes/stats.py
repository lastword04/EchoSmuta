from fastapi import APIRouter, Depends, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ..deps.stats import get_get_character_city_trade_stats_use_case
from ..schemas import CharacterCityTradeStatsReadSchema
from ..use_cases.stats.get_character_city_trade_stats import (
    GetCharacterCityTradeStatsUseCaseProtocol,
)

router = APIRouter()


@router.get('/city-shop/stats', response_model=CharacterCityTradeStatsReadSchema)
async def get_character_city_trade_stats(
    location_slug: str | None = Query(None, min_length=1, max_length=128, description="Optional location slug from frontend"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharacterCityTradeStatsUseCaseProtocol = Depends(get_get_character_city_trade_stats_use_case)
) -> CharacterCityTradeStatsReadSchema:
    return await use_case(user, location_slug=location_slug)
