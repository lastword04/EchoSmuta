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


# CHARACTER INFO
class CharacterInfoBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Id of character")
    name: Optional[str] = Field(None, max_length=25, description="Additional name for character info")
    country: Optional[str] = Field(None, max_length=25, description="Country for character")
    city: Optional[str] = Field(None, max_length=25, description="City for character")
    info: Optional[str] = Field(None, max_length=5000, description="Info about character")

class CharacterInfoCreateSchema(CharacterInfoBaseSchema, CreateBaseModel):
    pass

class CharacterInfoUpdateSchema(CharacterInfoBaseSchema, CreateBaseModel):
    pass

class CharacterInfoUpdateDBSchema(CharacterInfoBaseSchema, UpdateBaseModel):
    pass

class CharacterInfoReadSchema(CharacterInfoBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Id of character info")

class CharacterFullInfoSchema(BaseModel):
    info: CharacterReadSchema
    additional_info: CharacterInfoReadSchema
    categories_stats: BaseCategoryStatsSchema

class CharacterInfoRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=25, description="Additional name for character info")
    country: Optional[str] = Field(None, max_length=25, description="Country for character")
    city: Optional[str] = Field(None, max_length=25, description="City for character")
    info: Optional[str] = Field(None, max_length=5000, description="Info about character")
