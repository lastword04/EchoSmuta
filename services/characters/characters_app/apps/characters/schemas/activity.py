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


class CharacterActivityBaseSchema(BaseModel):
    action_type: ActionType = Field(
        ..., 
        description="Type of action performed by the character"
    )
    action_details: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Additional details about the action in JSON format"
    )

class CharacterActivityCreateSchema(CharacterActivityBaseSchema, CreateBaseModel):
    pass

class CharacterActivityCreateDBSchema(CharacterActivityCreateSchema):
    character_id: uuid.UUID = Field(
        ..., 
        description="UUID of the character performing the action"
    )

class CharacterActivityUpdateSchema(BaseModel):
    action_type: Optional[ActionType] = Field(
        None, 
        description="Type of action performed by the character"
    )
    action_details: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Additional details about the action in JSON format"
    )

class CharacterActivityUpdateDBSchema(CharacterActivityUpdateSchema, UpdateBaseModel):
    character_id: uuid.UUID = Field(
        ..., 
        description="UUID of the character performing the action"
    )

class CharacterActivityReadSchema(CharacterActivityBaseSchema, TimestampMixin):
    character_id: uuid.UUID = Field(
        ..., 
        description="UUID of the character performing the action"
    )
    id: uuid.UUID = Field(
        ..., 
        description="Unique identifier of the activity record"
    )
