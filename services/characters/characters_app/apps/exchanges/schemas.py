import uuid
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from shared.schemas.base import (
    CreateBaseModel, UpdateBaseModel, TimestampMixin,
    PaginationResultSchema
)
from .enums import Currency
from .exceptions import CurrencyValidationError

# EXCHANGE SETTINGS SCHEMAS
class ExchangeSettingsBaseSchema(BaseModel):
    min_ducats_on_slot: int = Field(..., ge=0)
    max_ducats_on_slot: int = Field(..., ge=0)
    min_gold_on_slot: int = Field(..., ge=0)
    max_gold_on_slot: int = Field(..., ge=0)
    min_course_on_gold: int = Field(..., ge=0)
    max_course_on_gold: int = Field(..., ge=0)
    seller_on_ducats_tax: float = Field(..., ge=0.0)

class ExchangeSettingsCreateSchema(ExchangeSettingsBaseSchema, CreateBaseModel):
    pass

class ExchangeSettingsUpdateSchema(ExchangeSettingsBaseSchema):
    pass

class ExchangeSettingsUpdateDBSchema(ExchangeSettingsBaseSchema, UpdateBaseModel):
    pass

class ExchangeSettingsReadSchema(ExchangeSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID

# SLOT SCHEMAS
class SlotRequestSchema(BaseModel):
    value: Decimal = Field(..., gt=0, le=Decimal("9999999.99"), description="Amount of ducats or gold in the slot")
    currency: Currency = Field(..., description="Type of currency: gold or ducats")
    course: int = Field(..., gt=0, le=9999999, description="Course. Amount of ducats per 1 gold")

    @model_validator(mode='after')
    def validate_value_precision(self) -> 'SlotRequestSchema':
        # Единое правило для обеих валют: не больше 2 знаков после запятой
        decimal_value = Decimal(str(self.value))
        if decimal_value.as_tuple().exponent < -2:
            raise CurrencyValidationError(
                detail="Currency amount cannot have more than 2 decimal places",
                field_name="value",
                provided_value=self.value,
                max_decimal_places=2,
                currency_type=self.currency,
            )
        return self


class SlotBaseSchema(BaseModel):
    ducats: Decimal = Field(..., gt=0, description="Amount of ducats in the slot")
    gold: Decimal = Field(..., gt=0, description="Amount of gold in the slot")

class SlotWithCurrencySchema(SlotBaseSchema):
    buy_for: Currency = Field(..., description="Currency type for buying the slot")

class SlotWithSellerSchema(SlotBaseSchema):
    seller_id: uuid.UUID = Field(..., description="ID of the character selling the slot")

# Create schemas
class SlotCreateSchema(SlotBaseSchema, CreateBaseModel):
    sell: Currency = Field(..., description="Currency type for selling the slot")

class SlotCreateDBSchema(SlotWithCurrencySchema, SlotWithSellerSchema, CreateBaseModel):
    pass

# Update schemas
class SlotUpdateSchema(SlotWithCurrencySchema, SlotWithSellerSchema):
    pass

class SlotUpdateDBSchema(SlotWithCurrencySchema, SlotWithSellerSchema, UpdateBaseModel):
    pass

# Read schemas
class SlotReadBaseSchema(SlotWithCurrencySchema):
    id: uuid.UUID = Field(..., description="Unique identifier for the slot")
    number: int = Field(..., description="Slot number")

class SlotReadDBSchema(SlotReadBaseSchema, SlotWithSellerSchema, TimestampMixin):
    pass

class SlotReadSchema(SlotReadBaseSchema, TimestampMixin):
    is_owner: bool = Field(..., description="Indicates if the requesting user is the owner of the slot")

class SlotPaginationResultSchema(PaginationResultSchema[SlotReadSchema]):
    pass

class BuySlotResponse(BaseModel):
    success: bool
    slot_id: uuid.UUID
    buyer_id: uuid.UUID
    currency_used: Currency
    amount_paid: Decimal
    currency_received: Currency
    amount_received: Decimal