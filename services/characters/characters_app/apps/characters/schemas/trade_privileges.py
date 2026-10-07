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


class CharacterTradePrivilegeUpdateSchema(BaseModel):
    gold_trade_enabled: bool


class CharacterTradePrivilegeReadSchema(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    gold_trade_enabled: bool
    updated_by_admin_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CharacterTradePrivilegesInternalSchema(BaseModel):
    gold_trade_enabled: bool
