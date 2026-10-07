from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from decimal import Decimal
from shared.schemas.base import (
    CreateBaseModel, UpdateBaseModel, TimestampMixin
)
from shared.enums import Race
from shared.schemas.characters import CharacterBaseSchema, CharacterReadSchema
from shared.schemas.locations import LocationBaseSchema
from shared.schemas.category import BaseCategoryStatsSchema
from shared.enums import LocationType
from ..exceptions import CurrencyValidationError, EmptyTransferError
from ..enums import ActionType, CharacterSkillType


class InternalCharacterSearchItemSchema(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    location_slug: Optional[str] = None
    is_online: bool

    model_config = ConfigDict(from_attributes=True)


class InternalCharacterSearchResponseSchema(BaseModel):
    objects: list[InternalCharacterSearchItemSchema]
    count: int
