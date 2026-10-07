import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from typing import Optional
from shared.models import TimestampMixin
from ...core.db import Base
from .enums import MessageType

class Message(Base, TimestampMixin):
    __tablename__ = "chat_messages"
    
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    sender_name: Mapped[Optional[str]] = mapped_column(
        sa.String(21),
        nullable=True
    )

    message_type: Mapped[Optional[MessageType]] = mapped_column(
        sa.Enum(MessageType),
        nullable=True,
        index=True
    )

    room: Mapped[str] = mapped_column(
        sa.String(256),
        nullable=False,
        index=True
    )

    content: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False
    )

    original_content: Mapped[str] =  mapped_column(
        sa.Text,
        nullable=False
    )
    
    target_user_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        sa.ARRAY(sa.UUID(as_uuid=True)),
        nullable=True,
        default=None
    )

    target_user_names: Mapped[Optional[list[str]]] = mapped_column(
        sa.ARRAY(sa.String(21)),
        nullable=True,
        default=None
    )

    is_trade: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        index=True
    )

class Ignore(Base, TimestampMixin):
    __tablename__ = "chat_ignores"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    ignored_character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    __table_args__ = (
        sa.UniqueConstraint('character_id', 'ignored_character_id', name='uq_character_ignored_character'),
        sa.CheckConstraint('character_id != ignored_character_id', name='ck_character_not_equal_ignored'),
    )

class ChatSettings(Base, TimestampMixin):
    __tablename__ = "chat_settings"

    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True
    )

    # Общие настройки
    chat_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    clan_chat_is_blue: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)  # синий клан чат
    system_italic: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    font_size: Mapped[int] = mapped_column(sa.Integer, default=13, nullable=False)

    # Фильтр сообщений
    filter_only_me_and_my: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False) # Когда True - показывать только свои и приватные
    filter_system_messages: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False) # Когда True - показывать системные
    filter_trade_messages: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False) # Когда True - показывать системные
    filter_location_messages: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False) # Когда True - показывать чат локации в global

    # Кнопки чата
    show_journal: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    show_bell: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    show_translit: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    show_lastic: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    show_clear_screen: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    show_trade_messages_button: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    # Звуки
    sound_general_chat: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    sound_private_message: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    sound_clan_battle: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    sound_battle_start: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    sound_timeout: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

class FavoriteBells(Base, TimestampMixin):
    __tablename__ = "favorite_bells"
    
    character_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    code_bell: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False
    )