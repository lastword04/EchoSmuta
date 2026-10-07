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


class ReferralLink(Base, TimestampMixin):
    """
    Модель реферальной ссылки.
    """
    __tablename__ = 'referral_links'

    referrer_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )  # user_id

    referral_code: Mapped[str] = mapped_column(
        sa.String(64),
        nullable=False,
        unique=True,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True
    )

    max_uses: Mapped[Optional[int]] = mapped_column(
        sa.Integer,
        nullable=True
    )

    current_uses: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )

    # Relationships
    referrals: Mapped[list["Referral"]] = relationship(
        "Referral",
        back_populates="referral_link",
        lazy="select"
    )


class Referral(Base, TimestampMixin):
    """
    Модель реферала.
    """
    __tablename__ = 'referrals'

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    referrer_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )  # user_id of the referrer

    referred_user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )  # user_id of the referred user

    referral_link_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey('referral_links.id'),
        nullable=False,
        index=True
    )

    # Relationships
    referral_link: Mapped["ReferralLink"] = relationship(
        "ReferralLink",
        back_populates="referrals",
        lazy="select"
    )
