import uuid
from pydantic import BaseModel, Field
from typing import Optional
from shared.schemas.base import TimestampMixin, CreateBaseModel, UpdateBaseModel, PaginationResultSchema
from .enums import SenderStatus

class MailMessageBaseSchema(BaseModel):
    from_character_name: Optional[str] = Field(None, max_length=21)
    from_character_id: Optional[uuid.UUID] = None
    to_character_name: str = Field(..., max_length=21)
    to_character_id: uuid.UUID
    message: str = Field(..., max_length=1000)
    sender_status: SenderStatus = Field(..., description="Indicates whether the message was sent by a user or the system.")
    is_read: bool = Field(False, description="Is read message or not")

class MailMessageCreateSchema(MailMessageBaseSchema, CreateBaseModel):
    pass

class MailMessageUpdateSchema(MailMessageBaseSchema, UpdateBaseModel):
    pass

class MailMessageReadSchema(MailMessageBaseSchema, TimestampMixin):
    id: uuid.UUID

class MailMessageRequestCreateSchema(BaseModel):
    to_character_name: str = Field(..., max_length=21)
    message: str = Field(..., max_length=1000)

class MailMessagePaginationResultSchema(PaginationResultSchema[MailMessageReadSchema]):
    pass

class ReadStatusSchema(BaseModel):
    all_is_read: bool = Field(..., description="Is read all messages")

class MailRecieveSettingsBaseSchema(BaseModel):
    character_id: uuid.UUID
    is_block_send_mails: bool

class MailRecieveSettingsCreateSchema(MailRecieveSettingsBaseSchema, CreateBaseModel):
    pass

class MailRecieveSettingsUpdateSchema(MailRecieveSettingsBaseSchema, UpdateBaseModel):
    pass

class MailRecieveSettingsReadSchema(MailRecieveSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID
