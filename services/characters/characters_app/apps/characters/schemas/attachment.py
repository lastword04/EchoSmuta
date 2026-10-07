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


# Character Attachment Settings schemas
class CharacterAttachmentSettingsBaseSchema(BaseModel):
    attach_cost: int = Field(..., description="Cost to attach a character")
    attach_cost_per_level: int = Field(..., description="Cost to attach per level")
    detach_cost: int = Field(..., description="Cost to attach a character")
    detach_cost_per_level: int = Field(..., description="Cost to detach per level")

class CharacterAttachmentSettingsCreateSchema(CharacterAttachmentSettingsBaseSchema, CreateBaseModel):
    pass

class CharacterAttachmentSettingsUpdateSchema(CharacterAttachmentSettingsBaseSchema):
    pass

class CharacterAttachmentSettingsUpdateDBSchema(CharacterAttachmentSettingsBaseSchema, UpdateBaseModel):
    pass

class CharacterAttachmentSettingsReadSchema(CharacterAttachmentSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the character attachment settings")

    def calculate_attach_cost(self, character_level: int) -> int:
        """Рассчитать стоимость прикрепления персонажа"""
        return self.attach_cost + (self.attach_cost_per_level * character_level)

    def calculate_detach_cost(self, character_level: int) -> int:
        """Рассчитать стоимость открепления персонажа"""
        return self.detach_cost + (self.detach_cost_per_level * character_level)
