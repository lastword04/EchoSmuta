import uuid
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from shared.models import TimestampMixin
from ...core.db import Base


class RestRental(Base, TimestampMixin):
    """Активная аренда жилья/отдыха."""
    __tablename__ = "rest_rentals"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    room_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    days: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    
    rented_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True
    )


class RestRentalHistory(Base):
    """История аренд (минимальная)."""
    __tablename__ = "rest_rental_history"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    days: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    
    rented_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    expired_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )


class House(Base, TimestampMixin):
    """Частный дом: контейнер мебели и источник регенов."""
    __tablename__ = "houses"

    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    number: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    current_volume: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default="0")
    regen_multipliers: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {"health": 1.0, "mana": 1.0, "tiredness": 1.0},
        server_default='{"health": 1.0, "mana": 1.0, "tiredness": 1.0}'
    )
    wallpaper_photo_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True)


class HouseFurniture(Base, TimestampMixin):
    """Мебель, установленная в дом. Предмет остаётся в инвентаре владельца."""
    __tablename__ = "house_furniture"

    house_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("houses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True
    )

class HouseGuestRequest(Base, TimestampMixin):
    """Заявка на вход в дом (стук). Одна активная на пару (дом, гость)."""
    __tablename__ = "house_guest_requests"

    house_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("houses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, index=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "house_id", "character_id",
            name="uq_house_guest_requests_house_character",
        ),
    )


class HouseGuestSession(Base, TimestampMixin):
    """Гость внутри дома. Один гость — одновременно только один дом.
    Время входа — created_at из TimestampMixin."""
    __tablename__ = "house_guests"

    house_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("houses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )


class InventoryItemWorkAccumulator(Base, TimestampMixin):
    """Аккумулятор минут работы мебели для последующего конвертирования в wear."""
    __tablename__ = "inventory_item_work_accumulator"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )
    work_minutes: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=0.0,
        server_default="0.0"
    )