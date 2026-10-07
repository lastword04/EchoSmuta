from datetime import datetime
from enum import Enum
from decimal import Decimal
from typing import Any, Optional
import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.models import TimestampMixin
from shared.enums import Race, LocationType
from ....core.db import Base
from ..enums import ActionType, CharacterSkillType


class Character(Base, TimestampMixin):
    """
    Модель персонажа.
    """
    __tablename__ = 'characters'
    
    name: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False,
        unique=True,
        index=True
    )

    photo_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    location_slug: Mapped[Optional[str]] = mapped_column(
        sa.String(128),
        sa.ForeignKey('locations.slug'),
        nullable=True,
        index=True
    )

    is_male: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True
    )

    race: Mapped[Race] = mapped_column(
        sa.Enum(Race),
        nullable=False
    )

    experience: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    level: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    health: Mapped[float] = mapped_column(
    sa.Float,
    nullable=False,
    default=30.0
)

    max_health: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=30.0
    )

    tiredness: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=0.0
    )

    max_tiredness: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=1.0
    )

    endurance: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=5
    )

    mana: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=0.0
    )

    max_mana: Mapped[float] = mapped_column(
        sa.Float,
        nullable=False,
        default=0.0
    )

    intelligence: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    weight: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    max_weight: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    gold: Mapped[Decimal] = mapped_column(
        sa.Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0"
    )

    ducats: Mapped[Decimal] = mapped_column(
        sa.Numeric(18, 2),
        nullable=False,
        default=Decimal("3"),
        server_default="3"
    )
    
    power: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    agility: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    lucky: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    equipment_bonuses: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )

    mastership_sword: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    mastership_axe: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    mastership_hammer: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    
    is_main: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False
    )

    is_online: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False
    )

    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True
    )

    is_banned: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.false()
    )
    
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    
    scheduled_deletion_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
        index=True  # Для быстрого поиска при очистке
    )

    food_cooldown_until: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    rest_state: Mapped[Optional[str]] = mapped_column(
        sa.String(32),
        nullable=True,
        index=True
    )

    current_house_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    current_room_id: Mapped[str | None] = mapped_column(
        sa.String(128),
        nullable=True,
        index=True,
    )
