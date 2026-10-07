import uuid
from pydantic import BaseModel, Field
from typing import Optional
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin, PaginationResultSchema
from shared.schemas.chat import ChatSettingsBaseSchema
from shared.schemas.characters import CharacterSimpleInfoReadSchema
from .enums import MessageType


class MessageBaseSchema(BaseModel):
    sender_id: Optional[uuid.UUID] = Field(None, description="ID of the sender")
    sender_name: Optional[str] = Field(None, description="Name of the sender")
    message_type: Optional[MessageType] = Field(None, description="Type of the message")
    room: str = Field(..., description="Room identifier. May be equals any location slug, 'global' or 'private'")
    content: str = Field(..., max_length=800, description="Content of the message")
    target_user_ids: Optional[list[uuid.UUID]] = Field(None, description="List of target characters IDs")
    target_user_names: Optional[list[str]] = Field(None, description="List of target characters names")
    is_trade: bool = Field(..., description="Indicates if the message is a trade")

class MessageRequestSchema(BaseModel):
    content: str = Field(..., description="Content of the message")
    target_user_ids: Optional[list[uuid.UUID]] = Field(None, description="List of target user IDs")
    is_trade: bool = Field(False, description="Is trade this message or not")
    is_private: bool = Field(False, description="Is private this message or not")
    room: Optional[str] = None 

class MessageCreateSchema(MessageBaseSchema, CreateBaseModel):
    original_content: str = Field(..., description="Original content of the message")

class MessageUpdateSchema(MessageBaseSchema, UpdateBaseModel):
    pass

class MessageReadSchema(MessageBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the message")

class MessagePaginationReadSchema(PaginationResultSchema[MessageReadSchema]):
    pass


# Ignore schema
class IgnoreBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="ID of the character who ignores")
    ignored_character_id: uuid.UUID = Field(..., description="ID of the ignored character")

class IgnoreCreateSchema(IgnoreBaseSchema, CreateBaseModel):
    pass

class IgnoreUpdateSchema(IgnoreBaseSchema, UpdateBaseModel):
    pass

class IgnoreReadSchema(IgnoreBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the ignore relationship")

class IgnoreRequestSchema(BaseModel):
    ignored_character_id: uuid.UUID = Field(..., description="ID of the character to ignore")

# Chat settings schema
class ChatSettingsCreateSchema(ChatSettingsBaseSchema, CreateBaseModel):
    pass

class ChatSettingsUpdateSchema(ChatSettingsBaseSchema, CreateBaseModel):
    pass

class ChatSettingsUpdateDBSchema(ChatSettingsBaseSchema, UpdateBaseModel):
    pass


# Favorite bells
class FavoriteBellsBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Character id")
    code_bell: int = Field(..., description="Code of bell")

class FavoriteBellsRequestSchema(BaseModel):
    code_bell: int = Field(..., description="Code of bell")

class FavoriteBellsCreateSchema(FavoriteBellsBaseSchema, CreateBaseModel):
    pass

class FavoriteBellsUpdateSchema(FavoriteBellsBaseSchema, CreateBaseModel):
    pass

class FavoriteBellsUpdateDBSchema(FavoriteBellsBaseSchema, UpdateBaseModel):
    pass

class FavoriteBellsReadSchema(FavoriteBellsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="id favorite bells")


# Character schemas
class CharacterOnlineReadSchema(CharacterSimpleInfoReadSchema):
    is_ignored: bool = Field(..., description="Is gnored character for current character")

class CharacterOnlinePaginationSchema(PaginationResultSchema[CharacterOnlineReadSchema]):
    pass