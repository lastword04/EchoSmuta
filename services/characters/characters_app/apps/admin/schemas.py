from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal


class AdminCharacterReadSchema(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    race: str
    level: int
    experience: int
    gold: Decimal
    ducats: Decimal
    is_main: bool
    is_online: bool
    is_active: bool
    is_banned: bool
    location_slug: Optional[str] = None
    deactivated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminCharacterListSchema(BaseModel):
    objects: list[AdminCharacterReadSchema]
    count: int


class AdminCharacterSearchFilters(BaseModel):
    name: Optional[str] = None          # точное совпадение (без учёта регистра)
    name_like: Optional[str] = None     # частичное совпадение
    character_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"


class AdminChangeDucatsRequest(BaseModel):
    amount: Decimal = Field(..., description="Positive to add, negative to subtract")
    reason: Optional[str] = Field(None, max_length=255)


class AdminBanCharacterRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=255)
