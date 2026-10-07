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


class CharacterActivity(Base, TimestampMixin):

    __tablename__ = "characters_activity"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[ActionType] = mapped_column(sa.Enum(ActionType), nullable=False)
    action_details: Mapped[str] = mapped_column(sa.Text, nullable=True)
