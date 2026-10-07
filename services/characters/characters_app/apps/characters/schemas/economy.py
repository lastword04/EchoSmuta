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


class CharacterDucatsOperationRequest(BaseModel):
    operation_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=4)


class CharacterDucatsBalanceResponse(BaseModel):
    character_id: uuid.UUID
    ducats: Decimal


class CharacterDucatsOperationResponse(CharacterDucatsBalanceResponse):
    operation_id: uuid.UUID
    amount: Decimal
    operation_type: str


class CharacterCurrencyOperationRequest(BaseModel):
    operation_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    operation_type: Optional[str] = None
    source: Optional[str] = None
    counterparty_id: Optional[uuid.UUID] = None
    item_meta: Optional[dict[str, Any]] = None
    meta: Optional[dict[str, Any]] = None


class CharacterCurrencyOperationResponse(BaseModel):
    character_id: uuid.UUID
    operation_id: uuid.UUID
    amount: Decimal
    operation_type: str
    currency: str
    balance_after: Decimal

    model_config = ConfigDict(from_attributes=True)


class CharacterCurrencyOperationReadSchema(BaseModel):
    id: uuid.UUID
    operation_id: uuid.UUID
    character_id: uuid.UUID
    currency: str
    operation_type: str
    amount: Decimal
    balance_after: Decimal
    source: Optional[str] = None
    counterparty_id: Optional[uuid.UUID] = None
    item_meta: Optional[dict[str, Any]] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CharacterCurrencyOperationListSchema(BaseModel):
    objects: list[CharacterCurrencyOperationReadSchema]
    count: int


class CharacterCurrencyOperationCurrency(str, Enum):
    DUCATS = 'ducats'
    GOLD = 'gold'


class CharacterCurrencyOperationSortBy(str, Enum):
    CREATED_AT = 'created_at'


class SortOrder(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class CharacterCurrencyOperationFilters(BaseModel):
    source: str | None = None
    operation_type: str | None = None
    currency: CharacterCurrencyOperationCurrency | None = None
    counterparty_id: uuid.UUID | None = None
    character_id: uuid.UUID | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    start_date: datetime | None = Field(default=None, deprecated=True)
    end_date: datetime | None = Field(default=None, deprecated=True)
    sort_by: CharacterCurrencyOperationSortBy = CharacterCurrencyOperationSortBy.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode='after')
    def validate_date_range(self) -> 'CharacterCurrencyOperationFilters':
        if self.from_date is not None and self.start_date is not None:
            raise ValueError('Use either from_date or start_date, not both')
        if self.to_date is not None and self.end_date is not None:
            raise ValueError('Use either to_date or end_date, not both')

        effective_from_date = self.from_date or self.start_date
        effective_to_date = self.to_date or self.end_date
        if effective_from_date is not None and effective_to_date is not None and effective_from_date > effective_to_date:
            raise ValueError('from_date must be less than or equal to to_date')
        return self

    @property
    def effective_from_date(self) -> datetime | None:
        return self.from_date or self.start_date

    @property
    def effective_to_date(self) -> datetime | None:
        return self.to_date or self.end_date


# Transfer Value Character Settings schemas
class TransferValueCharactersSettingsBaseSchema(BaseModel):
    min_transfer_level: int = Field(..., description="Minimum level required to transfer a character")
    min_transfer_ducats: Decimal = Field(..., description="Minimum ducats required to transfer a character")
    min_transfer_gold: Decimal = Field(..., description="Minimum gold required to transfer a character")
    transfer_tax_percentage: float = Field(..., description="Tax percentage applied on character transfer")

class TransferValueCharactersSettingsCreateSchema(TransferValueCharactersSettingsBaseSchema, CreateBaseModel):
    pass

class TransferValueCharactersSettingsUpdateSchema(TransferValueCharactersSettingsBaseSchema):
    pass

class TransferValueCharactersSettingsUpdateDBSchema(TransferValueCharactersSettingsBaseSchema, UpdateBaseModel):
    pass

class TransferValueCharactersSettingsReadSchema(TransferValueCharactersSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the transfer value character settings")

class CharacterTransferRequestSchema(BaseModel):
    from_character_id: uuid.UUID = Field(..., description="Unique identifier of the character to be transferred")
    to_character_id: uuid.UUID = Field(..., description="Unique identifier of the target character to receive the character")
    offered_ducats: Decimal = Field(0.0, ge=0, le=Decimal("9999999.99"), description="Ducats offered for the character transfer")
    offered_gold: Decimal = Field(0.0, ge=0, le=Decimal("9999999.99"), description="Gold offered for the character transfer")

    @field_validator('offered_ducats', 'offered_gold')
    @classmethod
    def validate_currency_precision(cls, value: float, info) -> float:
        """Validate that currency has no more than 2 decimal places."""
        field_name = info.field_name
        
        if value < 0:
            raise CurrencyValidationError(
                detail="Currency amount cannot be negative",
                field_name=field_name,
                provided_value=value,
                currency_type=field_name.replace('offered_', '')
            )
        
        decimal_value = Decimal(str(value))
        if decimal_value.as_tuple().exponent < -2:
            raise CurrencyValidationError(
                detail="Currency amount cannot have more than 2 decimal places",
                field_name=field_name,
                provided_value=value,
                max_decimal_places=2,
                currency_type=field_name.replace('offered_', '')
            )
        
        return value
    
    @model_validator(mode='after')
    def validate_transfer_amounts(self) -> 'CharacterTransferRequestSchema':
        """Validate that at least one currency amount is greater than 0."""
        if self.offered_gold <= 0.0 and self.offered_ducats <= 0.0:
            raise EmptyTransferError(
                offered_gold=self.offered_gold,
                offered_ducats=self.offered_ducats
            )
        return self

class TransferResult(BaseModel):
    """Result of character transfer operation."""
    success: bool = Field(description="Whether transfer was successful")
    transferred_gold: Decimal = Field(description="Amount of gold transferred after tax")
    transferred_ducats: Decimal = Field(description="Amount of ducats transferred after tax")
    tax_applied_ducats: Decimal = Field(description="Tax amount for ducats")
    from_character_id: uuid.UUID = Field(description="Source character ID")
    to_character_id: uuid.UUID = Field(description="Target character ID")
    transaction_id: uuid.UUID = Field(description="Unique transaction identifier")
