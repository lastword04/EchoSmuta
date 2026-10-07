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


# LOCATIONS

class LocationCreateSchema(LocationBaseSchema, CreateBaseModel):
    pass

class LocationUpdateSchema(LocationBaseSchema):
    pass

class LocationUpdateDBSchema(LocationBaseSchema, UpdateBaseModel):
    pass


class LocationCharacterCountSchema(BaseModel):
    location_slug: str
    count: int
    type: LocationType

class CityBaseSchema(BaseModel):
    name: str = Field(..., max_length=128, description="Name of the city")
    serial_number: int = Field(..., description="Serial number of the city")


class CityCreateSchema(CityBaseSchema, CreateBaseModel):
    pass

class CityUpdateSchema(CityBaseSchema):
    pass

class CityUpdateDBSchema(CityBaseSchema, UpdateBaseModel):
    pass

class CityReadSchema(CityBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the city")
