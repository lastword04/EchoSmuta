import uuid
from typing import Union, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ApplyBuffSchema(BaseModel):
    """Схема для применения баффа"""
    character_id: uuid.UUID
    buff_type: str = Field(..., max_length=64)
    value: Union[int, float]
    duration_seconds: int = Field(default=0, ge=0)
    source: str = Field(default="unknown", max_length=64)
    source_name: str | None = Field(default=None, max_length=255)


class RemoveBuffSchema(BaseModel):
    """Схема для удаления баффа"""
    character_id: uuid.UUID
    buff_type: str


class CharacterBuffReadSchema(BaseModel):
    """Схема для чтения баффа"""
    id: uuid.UUID
    character_id: uuid.UUID
    buff_type: str
    value: Union[int, float]
    duration_seconds: int
    expires_at: datetime | None
    source: str
    source_name: str | None = None
    is_active: bool
    stack_count: int
    
    model_config = ConfigDict(from_attributes=True)


class CharacterBuffsResponseSchema(BaseModel):
    """Ответ со списком баффов"""
    character_id: uuid.UUID
    buffs: list[CharacterBuffReadSchema]


class FoodEffectSchema(BaseModel):
    """Один эффект еды"""
    effect_type: str  # "hp_restore" или "stamina_restore_percent"
    value: Union[int, float]


class ConsumeFoodSchema(BaseModel):
    """Схема для применения еды"""
    character_id: uuid.UUID
    effects: list[FoodEffectSchema]
    cooldown_seconds: int = Field(..., gt=0)
    required_location_slug: Optional[str] = None