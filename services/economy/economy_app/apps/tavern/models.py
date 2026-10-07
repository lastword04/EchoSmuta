from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa

from ...core.db import Base


class TavernMeal(Base):
    __tablename__ = "tavern_meals"

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    health_restore: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    tiredness_restore_percent: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    ducats_price: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False)
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    stock: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=500, server_default="500")
    default_stock: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=500, server_default="500")
    stock_period: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="0")
