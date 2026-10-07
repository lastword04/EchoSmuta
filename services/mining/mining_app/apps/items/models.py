import uuid
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from shared.enums import Race, ResultStatus
from shared.models import TimestampMixin

from ...core.db import Base
from .enums import EquipmentSlot, ItemBindingType, ItemCreatingStatus, ItemType


class Item(Base, TimestampMixin):

    __tablename__ = "items"

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, unique=True, index=True)

    item_type: Mapped[ItemType] = mapped_column(sa.Enum(ItemType), nullable=False)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)

    # Общие поля для всех товаров
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    weight: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    
    # Специфичные поля с NULL для неприменимых случаев
    race: Mapped[Race | None] = mapped_column(
        sa.Enum(Race), 
        nullable=True,
    )

    
    # JSON для гибких атрибутов
    parameters: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    ability_parameters: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Крафт информация
    craft_stages: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    craft_experience: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    min_shelf_life_days: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_shelf_life_days: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    min_output_quantity: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_output_quantity: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    minimal_level: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    is_stackable: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    can_sell: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    prices: Mapped[list["ItemPrice"]] = relationship(
        "ItemPrice",
        primaryjoin="Item.slug==ItemPrice.item_slug",
        foreign_keys="[ItemPrice.item_slug]",
        viewonly=True,
        lazy="select"
    )
    
    __table_args__ = (
        sa.Index(
            "ix_items_ability_parameters_gin",
            ability_parameters,
            postgresql_using="gin",
        ),
        sa.Index(
            "ix_items_parameters_gin",
            parameters,
            postgresql_using="gin",
        ),
    )

class ItemComponent(Base):
    __tablename__ = "item_components"
    
    item_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey('items.slug', ondelete='CASCADE'), nullable=False, index=True)
    resource_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey('resources.slug', ondelete='CASCADE'), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class ItemPrice(Base):
    __tablename__ = "item_prices"
    __table_args__ = (
        sa.UniqueConstraint('item_slug', 'quantity', name='uq_item_quantity'),
    )
    
    item_slug: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey('items.slug', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)

    item: Mapped["Item"] = relationship(
        "Item",
        primaryjoin="Item.slug==ItemPrice.item_slug",
        foreign_keys="[ItemPrice.item_slug]",
        viewonly=True,
        back_populates="prices"
    )
    

class CharacterRecipes(Base, TimestampMixin):
    __tablename__ = "character_recipes"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)

    item_slug: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey('items.slug', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )

    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)

    item: Mapped["Item"] = relationship(
        "Item",
        primaryjoin="Item.slug==CharacterRecipes.item_slug",
        foreign_keys="[CharacterRecipes.item_slug]",
        viewonly=True,
        lazy="select"
    )


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (
        sa.CheckConstraint(
            '(character_id IS NOT NULL AND shop_id IS NULL) OR (character_id IS NULL AND shop_id IS NOT NULL)',
            name='check_character_or_shop'
        ),
    )

    character_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    shop_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey('city_trading_shop.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey('deals.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    item_slug: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey('items.slug', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    expired_date: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True, index=True)
    used_count: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    wear: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    item_binding_type: Mapped[ItemBindingType] = mapped_column(
        sa.Enum(ItemBindingType),
        nullable=False,
        default=ItemBindingType.NONE,
        server_default=ItemBindingType.NONE.name,
    )

    item: Mapped["Item"] = relationship(
        "Item",
        primaryjoin="Item.slug==InventoryItem.item_slug",
        foreign_keys="[InventoryItem.item_slug]",
        viewonly=True,
        lazy="select"
    )


class CharacterEquipment(Base, TimestampMixin):
    __tablename__ = "character_equipment"
    __table_args__ = (
        sa.UniqueConstraint("character_id", "slot", name="uq_character_equipment_slot"),
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), nullable=False, index=True
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    slot: Mapped[EquipmentSlot] = mapped_column(sa.Enum(EquipmentSlot), nullable=False)

class ShopNumberCounter(Base):
    """Счетчик номеров магазинов для каждой локации"""
    __tablename__ = "shop_number_counters"
    
    # Переопределяем id из Base, используя location_slug как PRIMARY KEY
    id: Mapped[str] = mapped_column('location_slug', sa.String(128), primary_key=True)
    last_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)


class CityTradingShop(Base, TimestampMixin):
    __tablename__ = "city_trading_shop"
    __table_args__ = (
        sa.UniqueConstraint('location_slug', 'character_id', name='uq_location_character'),
        sa.UniqueConstraint('location_slug', 'number', name='uq_location_shop_number'),
    )
    
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    character_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    character_name: Mapped[str | None] = mapped_column(sa.String(21), nullable=True)
    name: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    description: Mapped[str] = mapped_column(sa.String(75), nullable=True)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    current_capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    photo_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    end_license: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True, index=True)
    number: Mapped[int] = mapped_column(sa.Integer, nullable=False)

class CityTradingShopSettings(Base):
    __tablename__ = "city_trading_shop_settings"

    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    tax: Mapped[float] = mapped_column(sa.Float, nullable=False)
    price_up_level: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

class CityTradingShopBuySettings(Base):
    __tablename__ = "city_trading_shop_buy_settings"

    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    min_level: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)


class SaleInventoryItem(Base, TimestampMixin):
    __tablename__ = "sale_inventory_items"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey('inventory_items.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)

    inventory_item: Mapped["InventoryItem"] = relationship(
        "InventoryItem",
        primaryjoin="InventoryItem.id==SaleInventoryItem.inventory_item_id",
        foreign_keys="[SaleInventoryItem.inventory_item_id]",
        viewonly=True,
        lazy="select"
    )



class ItemExperienceForLevel(Base):
    __tablename__ = "item_experience_for_level"

    experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True, index=True)
    success_rate_one: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)


class CharacterCityTradeStats(Base, TimestampMixin):
    __tablename__ = "character_city_trade_stats"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        sa.UniqueConstraint('character_id', 'location_slug', name='uq_character_city_trade_location'),
    )


class Building(Base):
    __tablename__ = "buildings"

    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, unique=True, index=True)
    city_trading_location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, unique=True, index=True)


class CharacterStartCreatingItem(Base, TimestampMixin):
    __tablename__ = "character_start_creating_items"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    item_slug: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey('items.slug', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    craft_stage: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)



class ItemsCreatingAction(Base, TimestampMixin):
    __tablename__ = "items_creating_actions"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey('buildings.location_slug', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    start_time: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now()
    )
    finish_time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    status: Mapped[ItemCreatingStatus] = mapped_column(
        sa.Enum(ItemCreatingStatus),
        nullable=False,
        default=ItemCreatingStatus.IN_PROGRESS
    )
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    result_status: Mapped[ResultStatus | None] = mapped_column(sa.Enum(ResultStatus), nullable=True)
    recived_item_slug: Mapped[str | None] = mapped_column(
        sa.String(128),
        sa.ForeignKey('items.slug', ondelete='CASCADE'),
        nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    craft_stage: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    lost_resource: Mapped[str | None] = mapped_column(
        sa.String(128),
        sa.ForeignKey('resources.slug', ondelete='CASCADE'),
        nullable=True
    )
    
class CraftingLicense(Base, TimestampMixin):
    __tablename__ = "crafting_licenses"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    end_date: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    number: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('character_id', 'location_slug', name='uq_character_crafting_license'),
        sa.UniqueConstraint('location_slug', 'number', name='uq_location_license_number'),
    )

class SaleHistory(Base, TimestampMixin):
    __tablename__ = "sale_history"
    __table_args__ = (
        sa.Index("ix_sale_history_seller", "seller_character_id", "created_at"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("city_trading_shop.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    seller_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    buyer_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)
    buyer_name: Mapped[str] = mapped_column(sa.String(21), nullable=False)
    item_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
