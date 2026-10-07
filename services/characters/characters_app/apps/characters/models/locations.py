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


class City(Base):
    __tablename__ = 'cities'

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    serial_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)

class Location(Base):
    __tablename__ = 'locations'

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False, index=True)
    type: Mapped[LocationType] = mapped_column(sa.Enum(LocationType), nullable=False, default=LocationType.OTHER, index=True)
    city_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey('cities.id'),
        nullable=False,
        index=True
    )
    serial_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)
