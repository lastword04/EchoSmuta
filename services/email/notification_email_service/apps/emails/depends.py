from fastapi import Depends, BackgroundTasks
from ...core.db import AsyncSession
from ...core.db import get_async_session
from ...settings import Settings, get_settings
from .repositories.email_logs import EmailLogRepositoryProtocol, EmailLogRepository
from .services.templates import PasswordTemplateServiceProtocol, PasswordTemplateService
from .services.email_sender import EmailSenderServiceProtocol, EmailSenderService
from .services.email_logs import EmailLogServiceProtocol, EmailLogService
from .use_cases.send_and_save_email import SendAndSaveEmailUseCaseProtocol, SendAndSaveEmailUseCase


def __get_email_log_repository(session: AsyncSession = Depends(get_async_session)
) -> EmailLogRepositoryProtocol:
    return EmailLogRepository(session)


def get_email_sender(settings: Settings = Depends(get_settings)) -> EmailSenderServiceProtocol:
    return EmailSenderService(settings.smtp)

def get_password_template_service(settings: Settings = Depends(get_settings)
) -> PasswordTemplateServiceProtocol:
    return PasswordTemplateService(settings.reset_password_template.dir, settings.reset_password_template.name)


def get_email_log_service(
        background_tasks: BackgroundTasks,
        repository: EmailLogRepositoryProtocol = Depends(__get_email_log_repository),
        password_template_service: PasswordTemplateServiceProtocol = Depends(get_password_template_service),
        email_sender: EmailSenderServiceProtocol = Depends(get_email_sender),
        settings: Settings = Depends(get_settings)
) -> EmailLogServiceProtocol:
    return EmailLogService(repository, email_sender, password_template_service, settings, background_tasks)


def get_send_and_save_email_use_case(
        email_log_service: EmailLogServiceProtocol = Depends(get_email_log_service)
) -> SendAndSaveEmailUseCaseProtocol:
    return SendAndSaveEmailUseCase(email_log_service)