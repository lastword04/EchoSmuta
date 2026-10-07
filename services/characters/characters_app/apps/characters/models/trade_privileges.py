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


class CharacterTradePrivilege(Base, TimestampMixin):
    __tablename__ = "character_trade_privileges"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    gold_trade_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, server_default=sa.false())
    updated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
