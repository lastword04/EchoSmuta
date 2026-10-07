import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from shared.schemas.base import PaginationResultSchema

from .enums import (
    DealAssetType,
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)


class DealReadSchema(BaseModel):
    id: uuid.UUID
    initiator_character_id: uuid.UUID
    partner_character_id: uuid.UUID
    location_slug: str
    status: DealStatus
    initiator_confirmed_at: datetime | None
    partner_confirmed_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancelled_by_character_id: uuid.UUID | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealCreateSchema(BaseModel):
    partner_character_id: uuid.UUID
    location_slug: str = Field(min_length=1, max_length=128)


class DealCurrencyOfferUpdateSchema(BaseModel):
    amount: Decimal = Field(ge=0, le=Decimal("9999999.99"), max_digits=18, decimal_places=2)
    operation_id: uuid.UUID


class DealResourceOfferUpdateSchema(BaseModel):
    amount: int = Field(gt=0, le=9999999)


class DealInventoryItemOfferCreateSchema(BaseModel):
    inventory_item_id: uuid.UUID
    amount: int = Field(gt=0, le=9999999)


class DealOfferReadSchema(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    character_id: uuid.UUID
    ducats_amount: Decimal
    ducats_escrowed: Decimal
    gold_amount: Decimal
    gold_escrowed: Decimal
    revision: int
    confirmed_revision: int | None

    model_config = ConfigDict(from_attributes=True)


class DealItemReadSchema(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    offer_id: uuid.UUID
    owner_character_id: uuid.UUID
    asset_type: DealAssetType
    resource_slug: str | None
    inventory_item_id: uuid.UUID | None
    amount: int
    item_snapshot: dict | None

    model_config = ConfigDict(from_attributes=True)


class DealDetailSchema(DealReadSchema):
    offers: list[DealOfferReadSchema]
    items: list[DealItemReadSchema]


class DealListSchema(PaginationResultSchema[DealReadSchema]):
    pass


class NearbyPartnerSchema(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    location_slug: str | None


class DealResourceReservationReadSchema(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    deal_item_id: uuid.UUID
    character_id: uuid.UUID
    resource_slug: str
    amount: int
    status: ResourceReservationStatus

    model_config = ConfigDict(from_attributes=True)


class DealLedgerOperationReadSchema(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    operation_id: uuid.UUID
    operation_kind: DealLedgerOperationKind
    character_id: uuid.UUID
    counterparty_id: uuid.UUID | None
    currency: DealCurrency
    amount: Decimal
    status: DealLedgerOperationStatus
    payload: dict | None

    model_config = ConfigDict(from_attributes=True)


class TradeLicenseReadSchema(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class TradeLicenseStatusSchema(BaseModel):
    character_id: uuid.UUID
    active: bool
    end_date: datetime | None
    deal_tax_rate: Decimal
    exchange_tax_rate: Decimal


class CompletingDealListSchema(PaginationResultSchema[DealReadSchema]):
    pass
