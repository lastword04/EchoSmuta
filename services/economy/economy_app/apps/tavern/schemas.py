import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    health_restore: float
    tiredness_restore_percent: float
    ducats_price: Decimal
    stock: int


class TavernMenuSchema(BaseModel):
    meals: list[MealRead]
    next_rotation_at: datetime


class BuyMealRequest(BaseModel):
    meal_id: uuid.UUID
