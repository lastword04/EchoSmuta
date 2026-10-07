
import uuid
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..enums import UserRole


class UserTokenDataReadSchema(BaseModel):
    user_id: uuid.UUID = Field(..., description="Id user in token")
    character_id: Optional[uuid.UUID] = Field(None, description="Character id for person. May be null, when user not in game")
    role: UserRole = Field(..., description="Role of the user")
    is_main: bool = Field(False, description="Is main character")
    expiration: datetime = Field(..., description="Expiration time of access token")