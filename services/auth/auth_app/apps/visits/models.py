import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from typing import Optional
from ...core.db import Base
from shared.models import TimestampMixin
from .enums import EventType

class NewUsersVisit(Base, TimestampMixin):
    __tablename__ = "new_users_visit"

    ip_address: Mapped[str] = mapped_column(
        sa.String(45),
        nullable=False,
        index=True
    )

    fingerprint: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False
    )

    refferal_name: Mapped[Optional[str]] = mapped_column(
        sa.String(21),
        nullable=True
    )

    is_registered: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        nullable=False        
    )

    character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
    )

    __table_args__ = (
        sa.UniqueConstraint('ip_address', 'character_id', name='uq_ip_char'),
    )


class SessionUsersEvent(Base, TimestampMixin):
    __tablename__ = "session_users_event"

    ip_address: Mapped[str] = mapped_column(
        sa.String(45),
        nullable=False
    )

    fingerprint: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
    )

    event_type: Mapped[EventType] = mapped_column(
        sa.Enum(EventType),
        nullable=False,
    )


