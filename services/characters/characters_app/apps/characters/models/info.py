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


class CharacterInfo(Base, TimestampMixin):
    __tablename__ = "characters_info"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    name: Mapped[Optional[str]] = mapped_column(
        sa.String(25),
        nullable=True
    )

    country: Mapped[Optional[str]] = mapped_column(
        sa.String(25),
        nullable=True
    )

    city: Mapped[Optional[str]] = mapped_column(
        sa.String(25),
        nullable=True
    )

    info: Mapped[Optional[str]] = mapped_column(
        sa.String(5000),
        nullable=True
    )
