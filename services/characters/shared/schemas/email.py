import uuid
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class EmailStatus(Enum):
    QUEUED = 'queued'
    SENT = 'sent'
    FAILED = 'failed'
    

class EmailSimpleBaseSchema(BaseModel):
    to_email: EmailStr = Field(..., description="Recipient's email address")


class EmailBaseSchema(EmailSimpleBaseSchema):
    template_name: str = Field(..., description="Email template name")


class EmailLogBaseSchema(EmailBaseSchema):
    status: EmailStatus
    error: Optional[str] = None


class EmailLogReadSchema(EmailLogBaseSchema):
    id: uuid.UUID


class EmailResetPasswordSchema(EmailSimpleBaseSchema):
    reset_link: str = Field(..., description="Password reset link to be included in the email")
    duration: int = Field(..., description="Duration in minutes for the password reset link validity")