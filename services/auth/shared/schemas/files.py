import uuid
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .base import TimestampMixin, CreateBaseModel


class FileBaseSchema(BaseModel):
    template_name: Optional[str] = None
    filename: Optional[str] = None


class FileCreateSchema(FileBaseSchema, CreateBaseModel):
    subdir: str = "default"

class FileListCreateSchema(BaseModel):
    files: list[FileCreateSchema]

class FileReadSchema(FileBaseSchema, TimestampMixin):
    id: uuid.UUID
    url: HttpUrl
    creator_user_id: uuid.UUID
    size: int
    content_type: str
    filename: str


class FilesListReadSchema(BaseModel):
    files: list[FileReadSchema]
    

class FileIdsSchema(BaseModel):
    ids: list[uuid.UUID]