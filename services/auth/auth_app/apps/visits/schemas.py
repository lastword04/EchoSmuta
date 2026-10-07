import uuid
from pydantic import BaseModel
from typing import Optional
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin 
from .enums import EventType

class NewUsersVisitBaseSchema(BaseModel):
    ip_address: str
    fingerprint: str
    refferal_name: Optional[str] = None
    is_registered: bool = False
    character_id: Optional[uuid.UUID] = None

class NewUsersVisitCreateSchema(NewUsersVisitBaseSchema, CreateBaseModel):
    pass

class NewUsersVisitUpdateSchema(NewUsersVisitBaseSchema, UpdateBaseModel):
    pass

class NewUsersVisitReadSchema(NewUsersVisitBaseSchema, TimestampMixin):
    id: uuid.UUID

class NewUsersVisitRequestSchema(BaseModel):
    refferal_name: Optional[str]
    fingerprint: str


class SessionUserEventBaseSchema(BaseModel):
    ip_address: str
    fingerprint: str
    character_id: uuid.UUID
    event_type: EventType


class SessionUserEventCreateSchema(SessionUserEventBaseSchema, CreateBaseModel):
    pass

class SessionUserEventUpdateSchema(SessionUserEventBaseSchema, UpdateBaseModel):
    pass

class SessionUserEventReadSchema(SessionUserEventBaseSchema, TimestampMixin):
    id: uuid.UUID


class SessionUserEventRequestSchema(BaseModel):
    fingerprint: str