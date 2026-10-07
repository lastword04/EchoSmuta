import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.models import TimestampMixin

from ....core.db import Base
from .enums import (
    DealAssetType,
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"
    __table_args__ = (
        sa.CheckConstraint("initiator_character_id <> partner_character_id", name="different_participants"),
    )

    initiator_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    partner_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    status: Mapped[DealStatus] = mapped_column(sa.Enum(DealStatus), nullable=False, default=DealStatus.DRAFT, index=True)
    initiator_confirmed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    partner_confirmed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    cancelled_by_character_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, index=True)


class DealOffer(Base, TimestampMixin):
    __tablename__ = "deal_offers"
    __table_args__ = (
        sa.UniqueConstraint("deal_id", "character_id", name="uq_deal_offer_character"),
        sa.CheckConstraint("ducats_amount >= 0", name="ck_deal_offers_ducats_amount_positive"),
        sa.CheckConstraint("ducats_escrowed >= 0", name="ck_deal_offers_ducats_escrowed_positive"),
        sa.CheckConstraint("gold_amount >= 0", name="ck_deal_offers_gold_amount_positive"),
        sa.CheckConstraint("gold_escrowed >= 0", name="ck_deal_offers_gold_escrowed_positive"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    ducats_amount: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal(0), server_default="0")
    ducats_escrowed: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal(0), server_default="0")
    gold_amount: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal(0), server_default="0")
    gold_escrowed: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal(0), server_default="0")
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default="0")
    confirmed_revision: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)


class DealItem(Base, TimestampMixin):
    __tablename__ = "deal_items"
    __table_args__ = (
        sa.CheckConstraint(
            "(resource_slug IS NOT NULL AND inventory_item_id IS NULL) OR "
            "(resource_slug IS NULL AND inventory_item_id IS NOT NULL)",
            name="resource_xor_inventory_item",
        ),
        sa.CheckConstraint(
            "(asset_type = 'RESOURCE' AND resource_slug IS NOT NULL) OR "
            "(asset_type = 'INVENTORY_ITEM' AND inventory_item_id IS NOT NULL)",
            name="asset_type_matches_reference",
        ),
        sa.CheckConstraint("amount > 0", name="positive_amount"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    offer_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deal_offers.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    asset_type: Mapped[DealAssetType] = mapped_column(sa.Enum(DealAssetType), nullable=False, index=True)
    resource_slug: Mapped[str | None] = mapped_column(sa.ForeignKey("resources.slug"), nullable=True, index=True)
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("inventory_items.id"), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    item_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class DealResourceReservation(Base, TimestampMixin):
    __tablename__ = "deal_resource_reservations"
    __table_args__ = (sa.CheckConstraint("amount > 0", name="positive_amount"),)

    deal_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    deal_item_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deal_items.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    resource_slug: Mapped[str] = mapped_column(sa.ForeignKey("resources.slug"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[ResourceReservationStatus] = mapped_column(
        sa.Enum(ResourceReservationStatus),
        nullable=False,
        default=ResourceReservationStatus.ACTIVE,
        index=True,
    )


class DealLedgerOperation(Base, TimestampMixin):
    __tablename__ = "deal_ledger_operations"

    deal_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, unique=True, index=True)
    operation_kind: Mapped[DealLedgerOperationKind] = mapped_column(sa.Enum(DealLedgerOperationKind), nullable=False, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    currency: Mapped[DealCurrency] = mapped_column(sa.Enum(DealCurrency), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    status: Mapped[DealLedgerOperationStatus] = mapped_column(
        sa.Enum(DealLedgerOperationStatus),
        nullable=False,
        default=DealLedgerOperationStatus.PENDING,
        index=True,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class TradeLicense(Base, TimestampMixin):
    __tablename__ = "trade_licenses"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, unique=True, index=True)
    end_date: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, index=True)
