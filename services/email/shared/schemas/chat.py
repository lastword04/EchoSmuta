import uuid
from pydantic import BaseModel, Field, field_validator
from .base import TimestampMixin

class ChatSettingsBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="ID of the character")

    # Общие настройки
    chat_enabled: bool = Field(default=True, description="Whether chat is enabled")
    clan_chat_is_blue: bool = Field(default=False, description="Whether clan chat is blue")
    system_italic: bool = Field(default=False, description="Whether system messages are italic")
    font_size: int = Field(default=13, ge=13, le=16, description="Font size between 13 and 16")

    # Фильтр сообщений
    filter_only_me_and_my: bool = Field(default=False, description="Filter to show only my and my clan messages")
    filter_system_messages: bool = Field(default=True, description="Whether to show system messages")
    filter_trade_messages: bool = Field(default=False, description="Whether to show trade messages")
    filter_location_messages: bool = Field(default=False, description="Whether to show location messages in global chat")

    # Кнопки чата
    show_journal: bool = Field(default=True, description="Show journal button")
    show_bell: bool = Field(default=True, description="Show bell button")
    show_translit: bool = Field(default=False, description="Show translit button")
    show_lastic: bool = Field(default=True, description="Show lastic button")
    show_clear_screen: bool = Field(default=False, description="Show clear screen button")
    show_trade_messages_button: bool = Field(default=False, description="Show trade messages button")

    # Звуки
    sound_general_chat: bool = Field(default=False, description="Sound for general chat")
    sound_private_message: bool = Field(default=False, description="Sound for private messages")
    sound_clan_battle: bool = Field(default=False, description="Sound for clan battle")
    sound_battle_start: bool = Field(default=False, description="Sound for battle start")
    sound_timeout: bool = Field(default=False, description="Sound for timeout")

    # Валидация font_size
    @field_validator('font_size')
    def validate_font_size(cls, v):
        if v < 13 or v > 16:
            raise ValueError('font_size must be between 13 and 16')
        return v


class ChatSettingsDefaultCreateSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="ID of the character")
    is_main: bool = Field(..., description="Is main character")
    character_name: str = Field(..., description="name of character")
    
class ChatSettingsReadSchema(ChatSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the chat settings")
