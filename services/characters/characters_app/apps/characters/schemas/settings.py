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


# RaceSettings schemas
class RaceSettingsBaseSchema(BaseModel):
    race: Race = Field(..., description="Race of the character")
    base_power: int = Field(..., description="Base power of the race")
    base_agility: int = Field(..., description="Base agility of the race")
    base_lucky: int = Field(..., description="Base luck of the race")


class RaceSettingsCreateSchema(RaceSettingsBaseSchema, CreateBaseModel):
    pass


class RaceSettingsUpdateSchema(RaceSettingsBaseSchema):
    pass


class RaceSettingsUpdateDBSchema(RaceSettingsBaseSchema, UpdateBaseModel):
    pass


class RaceSettingsReadSchema(RaceSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the race settings")


# GlobalCharacterSettings schemas
class GlobalCharacterSettingsBaseSchema(BaseModel):
    default_experience: int = Field(..., description="Default experience for characters")
    default_level: int = Field(..., description="Default level for characters")
    default_health: float = Field(..., description="Default health for characters")
    default_max_health: float = Field(..., description="Default max health for characters")
    default_mana: float = Field(..., description="Default mana for characters")
    default_max_mana: float = Field(..., description="Default max mana for characters")    
    default_tiredness: float = Field(..., description="Default tiredness for characters")
    default_max_tiredness: float = Field(..., description="Default max tiredness for characters")
    default_endurance: int = Field(..., description="Default endurance for characters")
    default_weight: int = Field(..., description="Default weight for characters")
    default_max_weight: int = Field(..., description="Default max weight for characters")    
    default_intelligence: int = Field(..., description="Default intelligence for characters")
    default_weight: int = Field(..., description="Default weight for characters")
    default_max_weight: int = Field(..., description="Default max weight for characters")
    default_gold: Decimal = Field(..., description="Default gold for characters")
    default_ducats: Decimal = Field(..., description="Default ducats for characters")
    health_multiplier: float = Field(..., description="Health multiplier for characters")
    mana_multiplier: float = Field(..., description="Mana multiplier for characters")

    max_characters_on_user: int = Field(
        ..., description="Maximum number of characters allowed for a user"
        )


class GlobalCharacterSettingsCreateSchema(GlobalCharacterSettingsBaseSchema, CreateBaseModel):
    pass


class GlobalCharacterSettingsUpdateSchema(GlobalCharacterSettingsBaseSchema, UpdateBaseModel):
    pass

class GlobalCharacterSettingsUpdateDBSchema(GlobalCharacterSettingsBaseSchema, UpdateBaseModel):
    pass

class GlobalCharacterSettingsReadSchema(GlobalCharacterSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the global character settings")


# GlobalCharacterExperienceSettings schemas
class GlobalCharacterExperienceSettingsBaseSchema(BaseModel):
    level: int = Field(..., description="Level for characters")
    up: int = Field(..., description="Up for characters")
    experience: int = Field(..., description="Experience for characters")
    base: int = Field(..., description="Base for characters")
    weapon_skill: int = Field(..., description="Weapon Skill for characters")
    race_parameter: int = Field(..., description="Race Parameter for characters")
    skills: int = Field(..., description="Skills for characters")
    ducats: int = Field(..., description="Ducats for characters")
    endurance: int = Field(..., description="Endurance for characters")
    intelligence: int = Field(..., description="Intelligence for characters")

class GlobalCharacterExperienceSettingsCreateSchema(GlobalCharacterExperienceSettingsBaseSchema, CreateBaseModel):
    pass

class GlobalCharacterExperienceSettingsUpdateSchema(GlobalCharacterExperienceSettingsBaseSchema, UpdateBaseModel):
    pass

class GlobalCharacterExperienceSettingsUpdateDBSchema(GlobalCharacterExperienceSettingsBaseSchema, UpdateBaseModel):
    pass

class GlobalCharacterExperienceSettingsReadSchema(GlobalCharacterExperienceSettingsBaseSchema):
    id: uuid.UUID = Field(..., description="Unique identifier of the global character experience settings")


# UserCharacterSettings schemas
class UserCharacterSettingsBaseSchema(BaseModel):
    user_id: uuid.UUID = Field(..., description="Unique identifier of the user")
    max_characters: int = Field(..., description="Maximum number of characters allowed for the user")


class UserCharacterSettingsCreateSchema(UserCharacterSettingsBaseSchema, CreateBaseModel):
    pass

class UserCharacterSettingsUpdateSchema(UserCharacterSettingsBaseSchema):
    pass

class UserCharacterSettingsUpdateDBSchema(UserCharacterSettingsBaseSchema, UpdateBaseModel):
    pass

class UserCharacterSettingsReadSchema(UserCharacterSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the user character settings")


class CharacterCreationStatus(BaseModel):
    can_create: bool = Field(..., description="Indicates if the user can create a new character")
    current_characters: int = Field(..., description="Current number of characters the user has")
    max_characters: int = Field(..., description="Maximum number of characters allowed for the user")
