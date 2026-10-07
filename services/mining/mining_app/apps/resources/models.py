import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from shared.enums import ResultStatus
from shared.models import TimestampMixin

from ...core.db import Base
from .enums import MiningStatus


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(sa.String(32), nullable=True, index=True)
    weight: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    serial_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True, index=True)

class LocationResource(Base, TimestampMixin):
    __tablename__ = "location_resources"

    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    resource_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=False, index=True)
    chance: Mapped[float] = mapped_column(sa.Float, nullable=False)
    current_amount: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    max_amount: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    experience_on_resource: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    __table_args__ = (sa.UniqueConstraint('location_slug', 'resource_slug', name='uq_location_resource'),)

class MonsterLocaton(Base, TimestampMixin):
    __tablename__ = "monster_on_location"

    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True, unique=True)
    standart_monster_name: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True, unique=True)
    standart_monster_skin_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=False, index=True, unique=True)
    improved_monster_name: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True, unique=True)
    improved_monster_skin_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=False, index=True, unique=True)

class CharacterResource(Base, TimestampMixin):
    __tablename__ = "character_resources"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    resource_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    __table_args__ = (sa.UniqueConstraint('character_id', 'resource_slug', name='uq_character_resource'),)


class CharacterResourceOperation(Base, TimestampMixin):
    __tablename__ = "character_resource_operations"

    operation_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, unique=True, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    resource_slug: Mapped[str] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    amount: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class CharacterLocationStats(Base, TimestampMixin):
    __tablename__ = "characters_locations_stats"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    add_chance: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)

    __table_args__ = (sa.UniqueConstraint('character_id', 'location_slug', name='uq_character_location'),)


class LocationSettings(Base, TimestampMixin):
    __tablename__ = "location_settings"
    
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, unique=True, index=True)
    up_chance_for_unluck: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)


class ExperienceForLevel(Base):
    __tablename__ = "experience_for_level"

    experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True) 
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True, index=True)
    success_rate_one: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    success_rate_two: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    success_rate_three: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)

class MiningAction(Base, TimestampMixin):
    __tablename__ = "mining_actions"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    location_slug: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)

    start_time: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    finish_time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    status: Mapped[MiningStatus] = mapped_column(sa.Enum(MiningStatus), nullable=False, default=MiningStatus.IN_PROGRESS)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    result_status: Mapped[ResultStatus | None] = mapped_column(sa.Enum(ResultStatus), nullable=True)
    recived_resourse_slug: Mapped[str | None] = mapped_column(sa.String(128), sa.ForeignKey("resources.slug"), nullable=True)
    count_recived_resource: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
