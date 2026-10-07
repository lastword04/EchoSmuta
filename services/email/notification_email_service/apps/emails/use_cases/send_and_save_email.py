from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from shared.schemas.email import EmailResetPasswordSchema, EmailLogReadSchema
from ..services.email_logs import EmailLogServiceProtocol


class SendAndSaveEmailUseCaseProtocol(UseCaseProtocol[EmailLogReadSchema]):
    async def __call__(self: Self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        ...


class SendAndSaveEmailUseCase(SendAndSaveEmailUseCaseProtocol):
    def __init__(self: Self,
                  email_log_service: EmailLogServiceProtocol):
        self.email_log_service = email_log_service

    async def __call__(self: Self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        return await self.email_log_service.save_and_send_email(email)
