from fastapi import APIRouter, Depends, HTTPException

from shared.schemas.auth import UserTokenDataReadSchema

from ...core.db import Session
from ...core.depends import get_user_token_payload
from .depends import get_buy_meal_use_case, get_meals_use_case
from .schemas import BuyMealRequest, MealRead, TavernMenuSchema
from .use_cases.buy_meal import BuyMealUseCase
from .use_cases.get_meals import GetMealsUseCase

router = APIRouter(prefix="/api/economy/tavern", tags=["Tavern"])


@router.get("/meals", response_model=TavernMenuSchema)
async def tavern_meals(
    use_case: GetMealsUseCase = Depends(get_meals_use_case),
) -> TavernMenuSchema:
    """Список активных блюд Харчевни"""
    return await use_case()


@router.post("/buy")
async def tavern_buy(
    data: BuyMealRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuyMealUseCase = Depends(get_buy_meal_use_case),
) -> dict:
    if token.character_id is None:
        raise HTTPException(status_code=401, detail="Character is required")
    return await use_case(data.meal_id, token.character_id, session)
