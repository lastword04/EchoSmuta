import uuid
from datetime import datetime
from dataclasses import dataclass
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from shared.models import TimestampMixin
from ...core.db import Base


# Как модификатор влияет на стату
MOD_FLAT = "flat"              # прибавка: +5 к силе
MOD_PERCENT = "percent"        # процент от базовой статы: +20% к здоровью
MOD_MULTIPLIER = "multiplier"  # множитель результата: x2 к урону

# Где модификатор действует
CONTEXT_ALWAYS = "always"
CONTEXT_BATTLE = "battle_only"
CONTEXT_MAP = "map_only"

# Порядок применения по типам (пригодится в агрегаторе)
MODIFIER_PRIORITY = {MOD_FLAT: 1, MOD_PERCENT: 2, MOD_MULTIPLIER: 3}


class CharacterBuff(Base, TimestampMixin):
    """Баффы и дебаффы персонажа"""
    __tablename__ = "character_buffs"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Тип баффа: "hp_regen", "mana_regen", "strength_boost", "poison", etc.
    buff_type: Mapped[str] = mapped_column(
        sa.String(64),
        nullable=False,
        index=True
    )
    
    # Значение эффекта (сколько HP восстанавливает, сколько силы добавляет)
    value: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False
    )
    
    # Длительность в секундах (0 = мгновенный эффект)
    duration_seconds: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )
    
    # Когда истекает (для временных баффов)
    expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime,
        nullable=True
    )
    
    # Источник баффа: "potion", "food", "equipment", "spell"
    source: Mapped[str] = mapped_column(
        sa.String(64),
        nullable=False,
        default="unknown"
    )

    source_name: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True
    )
    
    # Активен ли бафф
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True
    )
    
    # Для стекающихся баффов (например, несколько зелий силы)
    stack_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=1
    )


@dataclass
class StatModifier:
    """
    Форма одного модификатора в памяти. НЕ таблица в БД.
    Collector'ы строят их из своих таблиц, агрегатор применяет.
    """
    source_type: str     # откуда: "equipment", "buff", "dragon", "orb", ...
    source_id: str       # ID конкретного объекта (строка баффа, предмет, дракон)
    stat: str            # какая стата: "strength", "max_health", "lucky", ...
    value: float         # величина: 5 для flat, 20 для percent, 2 для multiplier
    modifier_type: str   # MOD_FLAT / MOD_PERCENT / MOD_MULTIPLIER
    context: str = CONTEXT_ALWAYS
    applied_at: datetime | None = None  # когда начал действовать