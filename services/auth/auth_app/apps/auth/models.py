import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from typing import Optional
from ...core.db import Base
from shared.models import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    is_main: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False
    )

    hashed_refresh_token: Mapped[str] = mapped_column(
        sa.String(128),
        nullable=False,
        index=True
    )


class PasswordResetTokens(Base, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True))
    token_hash: Mapped[str] = mapped_column(sa.String(128), nullable=False)

class AuthLog(Base, TimestampMixin):
    """
    Лог попыток входа (успешных и неудачных).
    """
    __tablename__ = "auth_logs"

    ip_address: Mapped[str] = mapped_column(
        sa.String(45),
        nullable=False,
        index=True
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )

    fingerprint: Mapped[Optional[str]] = mapped_column(
        sa.String(255),
        nullable=True
    )

    character_name: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False,
        index=True
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    success: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False
    )

    error_reason: Mapped[Optional[str]] = mapped_column(
        sa.String(255),
        nullable=True
    )