import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from typing_extensions import Self
from datetime import datetime
from shared.enums import Race
from shared.schemas.base import TimestampMixin, CreateBaseModel, UpdateBaseModel
from shared.schemas.characters import CharacterReadSchema, CharacterCreateSchema, CharacterSimpleReadSchema
from shared.schemas.users import UserReadSchema, UserCreateSchema
from shared.schemas.captcha import CaptchaVerificationRequest
from ..visits.enums import EventType
from ..visits.schemas import SessionUserEventRequestSchema


class LoginSchema(BaseModel):
    name: str = Field(..., description="Name of the character")
    # disabled max length for debug
    #TODO: uncomment this for production
    # password: str = Field(..., min_length=8, max_length=128, description="Password for the user account")
    password: str = Field(..., max_length=128, description="Password for the user account")
    fingerprint: str = Field(..., description="Fingerprint of the user device")

    def to_session_request_schema(self: Self) -> SessionUserEventRequestSchema:
        """Convert to SessionUserEventRequestSchema with proper field mapping"""
        return SessionUserEventRequestSchema(
            fingerprint=self.fingerprint
        )

class UserAndCharacterCreateSchema(CaptchaVerificationRequest):
    email: EmailStr = Field(..., description="Email of the user")
    # disabled max length for debug
    #TODO: uncomment this for production
    # password: str = Field(..., min_length=8, description="Password of the user")
    password: str = Field(..., description="Password of the user")
    source_of_knowledge: Optional[str] = Field(None, description="Source of knowledge of the user")
    name: str = Field(..., max_length=100, description="Name of the character")
    race: Race = Field(..., description="Race of the character")
    is_male: bool = Field(..., description="Gender of the character")
    referral_code: Optional[str] = Field(None, description="Referral code for the character")
    visit_id: uuid.UUID = Field(..., description="ID of the new user visit")
    fingerprint: str = Field(..., description="fingerprint of user")

    def to_user_create_schema(self: Self) -> UserCreateSchema:
        """Convert to UserCreateSchema with proper field mapping"""
        return UserCreateSchema(
            email=self.email,
            password=self.password,
            source_of_knowledge=self.source_of_knowledge
        )

    def to_character_create_schema(self: Self, user_id: uuid.UUID) -> CharacterCreateSchema:
        """Convert to CharacterCreateSchema with proper field mapping"""
        return CharacterCreateSchema(
            name=self.name,
            race=self.race,
            is_male=self.is_male,
            user_id=user_id,
            referral_code=self.referral_code
        )
    
    def to_session_request_schema(self: Self) -> SessionUserEventRequestSchema:
        """Convert to SessionUserEventRequestSchema with proper field mapping"""
        return SessionUserEventRequestSchema(
            fingerprint=self.fingerprint
        )

class UserAndCharacterReadSchema(BaseModel):
    user: UserReadSchema
    character: CharacterReadSchema


class RefreshTokenBaseSchema(BaseModel):
    user_id: uuid.UUID
    character_id: Optional[uuid.UUID]
    hashed_refresh_token: str
    is_main: bool

class RefreshTokenReadDBSchema(RefreshTokenBaseSchema, TimestampMixin):
    id: uuid.UUID


class RefreshTokenUpdateDBSchema(RefreshTokenBaseSchema, UpdateBaseModel):
    pass


class RefreshTokenCreateDBSchema(RefreshTokenBaseSchema, CreateBaseModel):
    pass


class TokenReadSchema(BaseModel):
    token: str
    expiration: datetime


class UserAndCharacterSimpleReadSchema(BaseModel):
    user: UserReadSchema
    character: Optional[CharacterSimpleReadSchema] = None


class AuthTokensSchema(BaseModel):
    access_token: TokenReadSchema = Field(..., description="Access token for the user")
    refresh_token: TokenReadSchema = Field(..., description="Refresh token for the user")


class AuthSchema(AuthTokensSchema):
    user: UserReadSchema = Field(..., description="User information")
    character: Optional[CharacterSimpleReadSchema] = Field(None, description="Character information")

    def to_user_and_character_read_schema(self: Self) -> UserAndCharacterReadSchema:
        """Convert to UserAndCharacterReadSchema with proper field mapping"""
        return UserAndCharacterSimpleReadSchema(
            user=self.user,
            character=self.character
        )
    
class PlayAuthSchema(AuthTokensSchema):
    character: CharacterReadSchema = Field(..., description="Character information")


class UserResetSchema(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResetTokenSchema(BaseModel):
    token: str
    minutes: int

class ResetTokenBaseSchema(BaseModel):
    user_id: uuid.UUID
    token_hash: str

class ResetTokenCreateSchema(CreateBaseModel, ResetTokenBaseSchema):
    pass

class ResetTokenUpdateSchema(UpdateBaseModel, ResetTokenBaseSchema):
    pass

class ResetTokenReadSchema(ResetTokenBaseSchema, TimestampMixin):
    id: uuid.UUID