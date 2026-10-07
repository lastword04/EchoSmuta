import uuid
from pydantic import BaseModel, EmailStr, Field
from shared.schemas.email import EmailLogBaseSchema, EmailSimpleBaseSchema
from ...core.schemas import CreateBaseModel, UpdateBaseModel


class EmailLogCreateSchema(EmailLogBaseSchema, CreateBaseModel):
    pass


class EmailLogUpdateSchema(EmailLogBaseSchema, UpdateBaseModel):
    pass


class EmailToSendSchema(EmailSimpleBaseSchema):
    id: uuid.UUID
    body: str
    subject: str = Field(..., description="Email subject for the email to be sent")

class PasswordTemplateSchema(BaseModel):
    subject: str = Field(..., description="Email subject for password reset")
    duration: int = Field(..., description="Duration in minutes for the password reset link validity")
    reset_link: str = Field(..., description="Password reset link to be included in the email")
    support_email: EmailStr = Field(..., description="Support email address for user assistance")