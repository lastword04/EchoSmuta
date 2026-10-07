import uuid
from pydantic import BaseModel, Field, EmailStr
from .base import CreateBaseModel, TimestampMixin
from ..enums import UserRole


class UserRoleSchema(BaseModel):
    role: UserRole = Field(..., description="Role of the user, e.g., USER, ADMIN")

class UserBaseSchema(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    is_active: bool = Field(default=True, description="Indicates if the user is active")


class UserCreateSchema(CreateBaseModel, UserBaseSchema):
    source_of_knowledge: str = Field(None, description="Source of knowledge for the user")
    # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(..., max_length=128, description="Password for the user account")


class UserLoginSchema(BaseModel):
    user_id: uuid.UUID = Field(..., description="Unique identifier of the user")
     # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(..., max_length=128, description="Password for the user account")


class UserReadSchema(TimestampMixin, UserBaseSchema, UserRoleSchema):
    id: uuid.UUID = Field(..., description="Unique identifier of the user")

class PasswordSchema(BaseModel):
     # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(..., max_length=128, description="Password for the user account")
