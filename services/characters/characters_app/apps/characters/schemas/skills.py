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


# CharacterAbilitySkills schemas
class CharacterAbilitySkillsBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Unique identifier of the character")
    count_stats: int = Field(0, description="Count of stats for the character")
    count_mastership: int = Field(0, description="Count of mastership for the character")

class CharacterAbilitySkillsCreateSchema(CharacterAbilitySkillsBaseSchema, CreateBaseModel):
    pass


class CharacterAbilitySkillsUpdateSchema(CharacterAbilitySkillsBaseSchema, UpdateBaseModel):
    pass

class CharacterAbilitySkillsUpdateDBSchema(CharacterAbilitySkillsBaseSchema, UpdateBaseModel):
    pass

class CharacterAbilitySkillsReadSchema(CharacterAbilitySkillsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the character ability skills")

# AppliedCharacterHistory schemas
class AppliedCharacterHistoryBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Unique identifier of the character")
    count_applied_power: int = Field(0, ge=0, description="Count of applied power for the user")
    count_applied_agility: int = Field(0, ge=0, description="Count of applied agility for the user")
    count_applied_lucky: int = Field(0, ge=0, description="Count of applied lucky for the user")
    count_applied_endurance: int = Field(0, ge=0, description="Count of applied endurance for the user")
    count_applied_intelligence: int = Field(0, ge=0, description="Count of applied intelligence for the user")
    count_applied_mastership_sword: int = Field(0, ge=0, description="Count of applied mastership sword for the user")
    count_applied_mastership_axe: int = Field(0, ge=0, description="Count of applied mastership axe for the user")
    count_applied_mastership_hammer: int = Field(0, ge=0, description="Count of applied mastership hammer for the user")
   

    def summarize(self):
        """
        Возвращает два значения:
        1. Сумму всех полей count по обычным навыкам.
        2. Сумму всех полей count по мастерствам оружия.
        """
        total_count_stats = sum([
            self.count_applied_power,
            self.count_applied_agility,
            self.count_applied_lucky,
            self.count_applied_endurance,
            self.count_applied_intelligence
        ])
        
        total_count_mastership = sum([
            self.count_applied_mastership_sword,
            self.count_applied_mastership_axe,
            self.count_applied_mastership_hammer,
        ])
        
        return total_count_stats, total_count_mastership


class AppliedCharacterHistoryCreateSchema(AppliedCharacterHistoryBaseSchema, CreateBaseModel):
    pass

class AppliedCharacterHistoryUpdateSchema(AppliedCharacterHistoryBaseSchema, CreateBaseModel):
    pass

class AppliedCharacterHistoryUpdateDBSchema(AppliedCharacterHistoryBaseSchema, UpdateBaseModel):
    pass

class AppliedCharacterHistoryReadSchema(AppliedCharacterHistoryBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the applied character history")

# CharacterDistributions schemas
class CharacterDistributionsBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Unique identifier of the character")
    count_distributions: int = Field(0, ge=0, description="Count distributions for the user")
    price: float = Field(..., description="Price of distributions for the user")
    skill_type: CharacterSkillType = Field(..., description="Type of skill changed")
    
class CharacterDistributionsCreateSchema(CharacterDistributionsBaseSchema, CreateBaseModel):
    pass

class CharacterDistributionsUpdateSchema(CharacterDistributionsBaseSchema, CreateBaseModel):
    pass

class CharacterDistributionsUpdateDBSchema(CharacterDistributionsBaseSchema, UpdateBaseModel):
    pass

class CharacterDistributionsReadSchema(CharacterDistributionsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the applied character history")

# AllCharacterDistributionInfo schemas
class AllCharacterDistributionInfo(BaseModel):    
    history: AppliedCharacterHistoryReadSchema = Field(..., description="Applied character distributions history")
    info: list[CharacterDistributionsReadSchema] = Field(..., description="List of character distributions")


class ChangeSkillsRequest(BaseModel):
    step: int = Field(..., ge=0, le=100)
    skill_type: CharacterSkillType = Field(..., description="Type of skill to change")

class ChangeSkillsResponse(BaseModel):
    total_cost: float = Field(..., description="Total cost for changing skills")
    skill_type: CharacterSkillType = Field(..., description="Type of skill changed")
    step: int = Field(..., description="Number of skill points changed")

# Equipment Bonuses Schemas

class EquipmentBonusesRequestSchema(BaseModel):
    """Схема запроса для пересчёта бонусов."""
    bonuses: dict

    model_config = ConfigDict(from_attributes=True)
