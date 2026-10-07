import uuid
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from shared.models import TimestampMixin
from ...core.db import Base

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    is_main: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    owner_character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    max_count_characters: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    is_send_notifications: Mapped[Optional[bool]] = mapped_column(sa.Boolean, nullable=True, default=False)
    is_receive_notifications: Mapped[Optional[bool]] = mapped_column(sa.Boolean, nullable=True, default=False)
    
    is_block_send_mails: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)

    __table_args__ = (
        sa.UniqueConstraint('name', 'owner_character_id', name='uq_name_character_owner'),
    )


class CategoryCharacter(Base, TimestampMixin):
    __tablename__ = "categories_characters"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True),
        sa.ForeignKey('categories.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    __table_args__ = (
        sa.UniqueConstraint('category_id', 'character_id', name='uq_category_character'),
    )




