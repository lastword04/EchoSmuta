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


class CharacterAttachmentSettings(Base):
    __tablename__ = 'character_attachment_settings'
    
    attach_cost: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=10)
    detach_cost: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=50)
    attach_cost_per_level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=5)
    detach_cost_per_level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=5)
