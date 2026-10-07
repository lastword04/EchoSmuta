import uuid
import logging
from typing import Protocol
from typing_extensions import Self
from shared.schemas.email import EmailResetPasswordSchema
from shared.schemas.users import UserReadSchema, PasswordSchema
from ....settings import Settings
from ..schemas import (
    UserResetSchema, ResetPasswordRequest,
    ResetTokenSchema
)
from ..adapters.users import UserServiceClientProtocol
from ..adapters.emails import EmailServiceClientProtocol
from .tokens import ResetTokenServiceProtocol, TokenServiceProtocol


logger = logging.getLogger(__name__)

class ResetPasswordServiceProtocol(Protocol):
    async def reset_password(self: Self, user: UserResetSchema) -> bool:
        ...
    
    async def confirm_reset_password(self: Self, passwordResetSchema: ResetPasswordRequest) -> bool:
        ...

    async def reset_password_via_token(self: Self, user_id: uuid.UUID, new_password: str) -> None:
        ...
        

class ResetPasswordService(ResetPasswordServiceProtocol):
    def __init__(self: Self, user_service: UserServiceClientProtocol,
                 mail_sender: EmailServiceClientProtocol,
                reset_password_token_service: ResetTokenServiceProtocol,
                token_service: TokenServiceProtocol,
                settings: Settings
                ):
        self.user_service = user_service
        self.reset_password_token_service = reset_password_token_service
        self.mail_sender = mail_sender
        self.token_service = token_service
        self.settings = settings


    async def reset_password(self: Self, user: UserResetSchema) -> bool:
        logger.info(f"Resetting password for user: {user.email}")
        try:
            user_data = await self.user_service.get_by_email(user.email)
            token = await self.reset_password_token_service.generate_reset_token(user_data.id)
            message = self._generate_email_message(user_data, token)
            logger.info(f"Reset password email sent to user: {user.email}")
            await self.mail_sender.send_reset_password(message)
        except Exception:
            logger.warning(f"User with email: {user.email} does not exist. Not sent message to email")
            return True
        return True


    async def confirm_reset_password(self: Self, passwordResetSchema: ResetPasswordRequest) -> bool:
        logger.debug(f"Confirming password reset for user: {passwordResetSchema.token}")
        token = passwordResetSchema.token
        token_data = await self.reset_password_token_service.get_by_token(token)
        new_pass = PasswordSchema(password=passwordResetSchema.new_password)

        await self.reset_password_via_token(token_data.user_id, new_pass)
        await self.reset_password_token_service.delete(token_data.id)
        return True

    async def reset_password_via_token(self: Self, user_id: uuid.UUID, new_password: PasswordSchema) -> None:
        updated_user = await self.user_service.change_password(user_id, new_password)
        await self.token_service.delete_all_by_user_id(updated_user.id)

    def _generate_email_message(self: Self, user: UserReadSchema, token: ResetTokenSchema) -> str:
        reset_url = f"{self.settings.frontend_url}/confirm-reset-password?token={token.token}"
        email_schema = EmailResetPasswordSchema(
            to_email=user.email,
            reset_link=reset_url,
            duration=self.settings.reset_token.expire_minutes // 60,
        )
        return email_schema
    

