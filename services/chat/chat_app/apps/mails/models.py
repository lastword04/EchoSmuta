import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from typing import Optional
from shared.models import TimestampMixin
from ...core.db import Base
from .enums import SenderStatus

class MailMessage(Base, TimestampMixin):
    __tablename__ = "mail_messages"
    
    from_character_name: Mapped[Optional[str]] = mapped_column(
        sa.String(256),
        nullable=True,
    )

    from_character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    sender_status: Mapped[SenderStatus] = mapped_column(
        sa.Enum(SenderStatus),
        nullable=False,
        index=True
    )

    to_character_name: Mapped[str] = mapped_column(
        sa.String(256),
        nullable=False,
    )

    to_character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    message: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False
    )

    is_read: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    is_active_recipient: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        index=True
    )

    is_active_sender: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        index=True
    )

class MailRecieveSettings(Base, TimestampMixin):
    __tablename__ = "mail_settings"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True,
        unique=True
    )

    is_block_send_mails: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False
    )