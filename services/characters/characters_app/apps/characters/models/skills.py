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


class CharacterAbilitySkills(Base):
    __tablename__ = "character_ability_settings"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    count_stats: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_mastership: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

class AppliedCharacterHistory(Base, TimestampMixin):
    __tablename__ = "applied_character_history"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    count_applied_power: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_agility: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_lucky: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_endurance: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_intelligence: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_mastership_sword: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_mastership_axe: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    count_applied_mastership_hammer: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

class CharacterDistributions(Base, TimestampMixin):
    __tablename__ = "character_distributions"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    count_distributions: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    price: Mapped[int] = mapped_column(sa.Float, nullable=False, default=0)
    skill_type: Mapped[CharacterSkillType] = mapped_column(sa.Enum(CharacterSkillType), index=True, nullable=False)

    __table_args__ = (
    sa.UniqueConstraint('character_id', 'skill_type', name='uq_character_skill_type'),
)
