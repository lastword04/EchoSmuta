import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthLogReadSchema(BaseModel):
    id: uuid.UUID
    ip_address: str
    user_agent: Optional[str]
    fingerprint: Optional[str]
    character_name: str
    user_id: Optional[uuid.UUID]
    character_id: Optional[uuid.UUID]
    success: bool
    error_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuthLogListSchema(BaseModel):
    objects: list[AuthLogReadSchema]
    count: int


class AuthLogFilters(BaseModel):
    character_name: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    character_id: Optional[uuid.UUID] = None
    success: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"
