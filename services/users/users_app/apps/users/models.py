import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from shared.models import TimestampMixin
from shared.enums import UserRole
from ...core.db import Base


class User(Base, TimestampMixin):
    """
    Модель пользователя.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        sa.String(100), nullable=False, unique=True, index=True
    )

    password: Mapped[str] = mapped_column(sa.String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)

    role: Mapped[UserRole] = mapped_column(sa.Enum(UserRole), nullable=False)


class UserAdditionalInformation(Base, TimestampMixin):
    """
    Дополнительная информация о пользователе.
    """

    __tablename__ = "user_additional_information"

    user_id: Mapped[sa.UUID] = mapped_column(
        sa.UUID(as_uuid=True), nullable=False, index=True
    )

    source_of_knowledge: Mapped[str] = mapped_column(sa.Text, nullable=True)


class ModeratorPermission(Base, TimestampMixin):
    """
    Право модератора. Хранит какое право выдано пользователю с ролью MODERATOR.
    """

    __tablename__ = "moderator_permissions"

    user_id: Mapped[sa.UUID] = mapped_column(
        sa.UUID(as_uuid=True), nullable=False, index=True
    )

    permission: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    granted_by: Mapped[sa.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "permission", name="uq_moderator_user_permission"
        ),
    )


__all__ = (
    "User",
    "UserAdditionalInformation",
    "ModeratorPermission",
)
