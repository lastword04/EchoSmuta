import uuid
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from shared.models import TimestampMixin
from ...core.db import Base
from .enums import MenuItem


class CharacterFastItem(Base, TimestampMixin):

    __tablename__ = "characters_fast_items"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("characters.id", ondelete="CASCADE"), unique=True, nullable=False, index=True) 
    first_item: Mapped[MenuItem] = mapped_column(sa.Enum(MenuItem), nullable=True)
    second_item: Mapped[MenuItem] = mapped_column(sa.Enum(MenuItem), nullable=True)

