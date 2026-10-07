import enum
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ...core.db import Base

class ResourceCategory(str, enum.Enum):
    SWAMP = "swamp"
    MINE = "mine"
    GEMS = "gems"
    LAKE = "lake"
    FOREST = "forest"
    SANDS = "sands"
    SKINS = "skins"

class ResourceSourceType(str, enum.Enum):
    RESOURCE_LOCATION = "RESOURCE_LOCATION"
    CITY_LOCATION = "CITY_LOCATION"
    OTHER = "OTHER"


class PoolType(str, enum.Enum):
    BUYOUT = "BUYOUT"
    LOCATIONS = "LOCATIONS"
    PLAYERS = "PLAYERS"


class LotType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class LotStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class TransactionType(str, enum.Enum):
    BUYOUT_BUY = "BUYOUT_BUY"
    BUYOUT_SELL = "BUYOUT_SELL"
    EXCHANGE_BUY = "EXCHANGE_BUY"
    EXCHANGE_SELL = "EXCHANGE_SELL"
    EXCHANGE_CANCEL = "EXCHANGE_CANCEL"
    ADMIN_RESET = "ADMIN_RESET"
    TAVERN_BUY = "TAVERN_BUY"


class PriceRecalculationStatus(str, enum.Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PriceRecalculationReason(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    ADMIN_RESET = "ADMIN_RESET"


class Resource(Base):
    __tablename__ = "economy_resources"
    external_resource_id: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(sa.String(512))
    source_type: Mapped[ResourceSourceType] = mapped_column(sa.Enum(ResourceSourceType), nullable=False, index=True)
    is_tradeable: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    base_sell_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    base_buy_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    min_sell_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    max_sell_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    min_buy_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    max_buy_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    category: Mapped[ResourceCategory] = mapped_column(sa.Enum(ResourceCategory), nullable=False, index=True)
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, index=True)


class CurrentPrice(Base):
    __tablename__ = "resource_current_prices"
    resource_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("economy_resources.id", ondelete="CASCADE"), unique=True)
    sell_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)  # цена продажи игроку
    buy_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)   # цена покупки у игрока
    previous_sell_price: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 2))
    previous_buy_price: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 2))
    last_recalculated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    next_recalculation_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class BuyoutStock(Base):
    __tablename__ = "buyout_stocks"
    resource_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("economy_resources.id", ondelete="CASCADE"), unique=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)


class PoolSnapshot(Base):
    __tablename__ = "resource_pool_snapshots"
    resource_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("economy_resources.id", ondelete="CASCADE"), index=True)
    recalculation_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("price_recalculations.id"), nullable=True, index=True)
    pool_type: Mapped[PoolType] = mapped_column(sa.Enum(PoolType), nullable=False)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class ExchangeLot(Base):
    __tablename__ = "exchange_lots"
    owner_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), index=True)
    lot_type: Mapped[LotType] = mapped_column(sa.Enum(LotType), nullable=False, index=True)
    status: Mapped[LotStatus] = mapped_column(sa.Enum(LotStatus), nullable=False, default=LotStatus.ACTIVE, index=True)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)  # ← цена всего бандла
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items: Mapped[list["ExchangeLotItem"]] = relationship(
        "ExchangeLotItem",
        back_populates="lot",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ExchangeLotItem(Base):
    __tablename__ = "exchange_lot_items"
    lot_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("exchange_lots.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("economy_resources.id"), index=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    
    __table_args__ = (
        sa.UniqueConstraint("lot_id", "resource_id", name="uq_exchange_lot_item"),
    )
    
    lot: Mapped["ExchangeLot"] = relationship("ExchangeLot", back_populates="items")
    
    __table_args__ = (
        sa.UniqueConstraint("lot_id", "resource_id", name="uq_exchange_lot_item"),
    )

class EconomyTransaction(Base):
    __tablename__ = "economy_transactions"

    transaction_type: Mapped[TransactionType] = mapped_column(sa.Enum(TransactionType), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("economy_resources.id"), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price_per_unit: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(sa.Numeric(24, 2), nullable=False)
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    seller_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    lot_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("exchange_lots.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PriceRecalculation(Base):
    __tablename__ = "price_recalculations"

    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    status: Mapped[PriceRecalculationStatus] = mapped_column(sa.Enum(PriceRecalculationStatus), nullable=False, index=True)
    reason: Mapped[PriceRecalculationReason] = mapped_column(sa.Enum(PriceRecalculationReason), nullable=False, index=True)
    next_recalculation_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class PriceRecalculationItem(Base):
    __tablename__ = "price_recalculation_items"

    recalculation_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("price_recalculations.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("economy_resources.id"), nullable=False, index=True)
    old_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    buyout_previous_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    buyout_current_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    locations_previous_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    locations_current_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    players_previous_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    players_current_quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    buyout_delta_percent: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    locations_delta_percent: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    players_delta_percent: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    price_delta_percent: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (sa.UniqueConstraint("recalculation_id", "resource_id", name="uq_price_recalculation_resource"),)


class EconomySchedulerState(Base):
    __tablename__ = "economy_scheduler_state"

    job_name: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, index=True)
    locked_until: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
