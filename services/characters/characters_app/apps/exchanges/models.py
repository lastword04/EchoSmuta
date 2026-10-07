import uuid
import sqlalchemy as sa
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from shared.models import TimestampMixin
from ...core.db import Base
from .enums import Currency


class ExchangeSettings(Base):
    __tablename__ = "exchange_settings"

    min_ducats_on_slot: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    max_ducats_on_slot: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    min_gold_on_slot: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    max_gold_on_slot: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    min_course_on_gold: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    max_course_on_gold: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    seller_on_ducats_tax: Mapped[float] = mapped_column(sa.Float, nullable=False)

class Slot(Base, TimestampMixin):
    __tablename__ = "slots"

    number: Mapped[int] = mapped_column(sa.Integer, sa.Sequence('slot_number_seq'), unique=True)
    ducats: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    gold: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    buy_for: Mapped[Currency] = mapped_column(sa.Enum(Currency), nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)