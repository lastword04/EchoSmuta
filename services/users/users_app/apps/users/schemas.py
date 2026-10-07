import uuid
from pydantic import BaseModel, Field
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin
from shared.schemas.users import UserBaseSchema, UserRoleSchema


class UserCreateDBSchema(UserBaseSchema, CreateBaseModel, UserRoleSchema):
    # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(
        ..., max_length=128, description="Password for the user account"
    )


class UserUpdateSchema(UserBaseSchema):
    pass


class UserUpdateDBSchema(UpdateBaseModel, UserBaseSchema):
    pass


class UserReadDBSchema(TimestampMixin, UserBaseSchema, UserRoleSchema):
    id: uuid.UUID = Field(..., description="Unique identifier of the user")
    # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(
        ..., max_length=128, description="Password for the user account"
    )


class UserAdditionalInformationBaseSchema(BaseModel):
    user_id: uuid.UUID = Field(..., description="Unique identifier of the user")
    source_of_knowledge: str = Field(
        None, description="Source of knowledge for the user"
    )


class UserAdditionalInformationCreateSchema(
    UserAdditionalInformationBaseSchema, CreateBaseModel
):
    pass


class UserAdditionalInformationReadSchema(
    TimestampMixin, UserAdditionalInformationBaseSchema
):
    id: uuid.UUID = Field(
        ..., description="Unique identifier of the additional information record"
    )


class UserAdditionalInformationUpdateSchema(
    UserAdditionalInformationBaseSchema, UpdateBaseModel
):
    pass


class PermissionListResponse(BaseModel):
    user_id: uuid.UUID
    permissions: list[str]
