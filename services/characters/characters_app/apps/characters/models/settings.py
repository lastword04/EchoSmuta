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


class RaceSettings(Base):
    """
    Настройки для каждой расы.
    """
    __tablename__ = 'race_settings'
    
    race: Mapped[Race] = mapped_column(sa.Enum(Race), unique=True, nullable=False)
    
    # Базовые параметры для расы
    base_power: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    base_agility: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    base_lucky: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    


class GlobalCharacterSettings(Base):
    """
    Глобальные настройки для всех персонажей.
    """
    __tablename__ = 'global_character_settings'
    
    # Дефолтные значения для всех параметров
    default_experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    default_level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    default_health: Mapped[float] = mapped_column(sa.Float, nullable=False, default=30.0)
    default_max_health: Mapped[float] = mapped_column(sa.Float, nullable=False, default=30.0)
    default_mana: Mapped[float] = mapped_column(sa.Float, nullable=False, default=10.0)
    default_max_mana: Mapped[float] = mapped_column(sa.Float, nullable=False, default=30.0)
    default_tiredness: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    default_max_tiredness: Mapped[float] = mapped_column(sa.Float, nullable=False, default=1.0)    
    default_weight: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    default_max_weight: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    default_endurance: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=5)    
    default_intelligence: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)       
    default_gold: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal("0"), server_default="0")
    default_ducats: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal("3"), server_default="3")

    # Множители
    health_multiplier: Mapped[float] = mapped_column(sa.Float, nullable=False, default=6.0)
    mana_multiplier: Mapped[float] = mapped_column(sa.Float, nullable=False, default=1.0)

    max_characters_on_user: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=4)


class GlobalCharacterExperienceSettings(Base):
    __tablename__ = "global_character_experience_settings"

    # Таблица опыта
    level: Mapped[int] = mapped_column(sa.Integer, nullable=False, index=True)
    up: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    experience: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True)
    base: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    weapon_skill: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    race_parameter: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    skills: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    ducats: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    endurance: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    intelligence: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class UserCharacterSettings(Base, TimestampMixin):
    """
    Настройки персонажа пользователя.
    """
    __tablename__ = 'user_character_settings'
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True
    )
    
    max_characters: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=3
    )


class TransferValueCharactersSettings(Base):
    """
    Настройки переноса значений персонажей.
    """
    __tablename__ = 'transfer_value_characters_settings'
    
    min_transfer_level: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    min_transfer_ducats: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal("3"), server_default="3")
    min_transfer_gold: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), nullable=False, default=Decimal("0.01"), server_default="0.01")
    transfer_tax_percentage: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.1)  # 10% tax
