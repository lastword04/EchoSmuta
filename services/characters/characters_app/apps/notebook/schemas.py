import uuid
from pydantic import BaseModel, Field
from typing import Optional
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin


class NotebookBaseSchema(BaseModel):
    text: Optional[str] = Field(None, description="Text in notebook")

class NotebookBaseDBSchema(NotebookBaseSchema):
    character_id: uuid.UUID = Field(..., description="Id character for notebook")
    
class NotebookCreateSchema(NotebookBaseSchema, CreateBaseModel):
    pass

class NotebookCreateDBSchema(NotebookBaseDBSchema, CreateBaseModel):
    pass

class NotebookUpdateSchema(NotebookBaseSchema, CreateBaseModel):
    pass

class NotebookUpdateDBSchema(NotebookBaseDBSchema, UpdateBaseModel):
    pass

class NotebookReadSchema(NotebookBaseDBSchema, TimestampMixin):
    id: uuid.UUID
