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


class ReferralBaseSchema(BaseModel):
    referrer_id: uuid.UUID = Field(..., description="Unique identifier of the referrer user")
    referred_user_id: uuid.UUID = Field(..., description="Unique identifier of the referred user")
    referral_link_id: uuid.UUID = Field(..., description="Unique identifier of the referral link")

class ReferralCreateSchema(ReferralBaseSchema, CreateBaseModel):
    pass

class ReferralUpdateSchema(ReferralBaseSchema):
    pass

class ReferralUpdateDBSchema(ReferralBaseSchema, UpdateBaseModel):
    pass

class ReferralReadSchema(ReferralBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the referral")

class ReferralWithNameReadSchema(ReferralReadSchema):
    referred_user_name: str = Field(..., description="Name of the referred user")

class ReferralLinkBaseSchema(BaseModel):
    referrer_id: uuid.UUID = Field(..., description="Unique identifier of the referrer user")
    referral_code: str = Field(..., max_length=64, description="Unique referral code")
    is_active: bool = Field(True, description="Indicates if the referral link is active")
    max_uses: Optional[int] = Field(None, description="Maximum number of uses for the referral link")
    current_uses: int = Field(0, description="Current number of uses for the referral link")

class ReferralLinkCreateSchema(ReferralLinkBaseSchema, CreateBaseModel):
    pass

class ReferralLinkUpdateSchema(ReferralLinkBaseSchema):
    pass

class ReferralLinkUpdateDBSchema(ReferralLinkBaseSchema, UpdateBaseModel):
    pass

class ReferralLinkReadSchema(ReferralLinkBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the referral link")
    
    def is_valid(self) -> bool:
        """Проверить, действительна ли реферальная ссылка"""
        return self.is_active and (self.max_uses is None or self.current_uses < self.max_uses)


class ReferralLinkWithReferralsReadSchema(ReferralLinkReadSchema):
    referrals: list[ReferralReadSchema] = Field(..., description="List of referrals associated with the referral link")

class ReferralLinkWithReferralsAndUrlReadSchema(ReferralLinkWithReferralsReadSchema):
    url: HttpUrl = Field(..., description="Full URL of the referral link")


class ReferralLinkResponseSchema(ReferralLinkReadSchema):
    url: HttpUrl = Field(..., description="Full URL of the referral link")
    referrals: list[ReferralWithNameReadSchema] = Field(..., description="List of referrals associated with the referral link")
