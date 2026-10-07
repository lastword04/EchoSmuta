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


class CurrencyType(str, Enum):
    DUCATS = "ducats"
    GOLD = "gold"


class CharacterCurrencyOperation(Base, TimestampMixin):
    __tablename__ = "character_currency_operations"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    operation_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, unique=True, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    currency: Mapped[str] = mapped_column(sa.String(16), nullable=False, default=CurrencyType.DUCATS.value, index=True)
    operation_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(sa.Numeric(18, 4), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(sa.Numeric(18, 4), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True, index=True)
    counterparty_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
    item_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
