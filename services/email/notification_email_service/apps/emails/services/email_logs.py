from fastapi import BackgroundTasks
import uuid
from typing import Protocol
import logging
from ....settings import Settings
from ..repositories.email_logs import EmailLogRepositoryProtocol
from ..schemas import(
    EmailLogCreateSchema, EmailLogUpdateSchema,
    EmailToSendSchema, PasswordTemplateSchema, 
) 
from .email_sender import EmailSenderServiceProtocol
from .templates import PasswordTemplateServiceProtocol
from shared.schemas.email import (
    EmailStatus, EmailResetPasswordSchema, EmailLogReadSchema
)


logger = logging.getLogger(__name__)

class EmailLogServiceProtocol(Protocol):
    repository: EmailLogRepositoryProtocol
    email_sender: EmailSenderServiceProtocol
    background_tasks: BackgroundTasks

    async def create_email_log(self, email_log: EmailLogCreateSchema) -> EmailLogReadSchema:
        ...

    async def update_email_log(self, email_log: EmailLogUpdateSchema) -> EmailLogReadSchema:
        ...

    async def save_and_send_email(self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        ...

    async def process_and_send_email(self, email_request: EmailResetPasswordSchema, email_log_id: uuid.UUID) -> None:
        ...

    async def send_email_and_update_status(self, email: EmailToSendSchema) -> None:
        ...

class EmailLogService(EmailLogServiceProtocol):
    def __init__(self, repository: EmailLogRepositoryProtocol,
                 email_sender: EmailSenderServiceProtocol,
                 password_template_service: PasswordTemplateServiceProtocol,
                 settings: Settings,
                 background_tasks: BackgroundTasks):
        self.repository = repository
        self.sender = email_sender
        self.password_template_service = password_template_service
        self.settings = settings
        self.tasks = background_tasks

    async def create_email_log(self, email_log: EmailLogCreateSchema) -> EmailLogReadSchema:
        return await self.repository.create(email_log)

    async def update_email_log(self, email_log: EmailLogUpdateSchema) -> EmailLogReadSchema:
        return await self.repository.update(email_log)

    async def save_and_send_email(self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        """Создает запись в БД и ставит задачу в очередь. Быстрый ответ клиенту."""
        logger.info(f"Creating email log for recipient: {email.to_email}")
        
        # Только создаем запись в БД
        email_log = EmailLogCreateSchema(
            to_email=email.to_email,
            template_name=self.settings.reset_password_template.name,
            status=EmailStatus.QUEUED
        )
        created_email_log = await self.repository.create(email_log)
        logger.info(f"Email log created with ID: {created_email_log.id}")
        
        # Всю остальную работу переносим в фон
        self.tasks.add_task(
            self.process_and_send_email,
            email_request=email,
            email_log_id=created_email_log.id
        )
        
        return created_email_log
    
    async def process_and_send_email(self, email_request: EmailResetPasswordSchema, email_log_id: uuid.UUID) -> None:
        """Фоновая задача: рендеринг шаблона + отправка письма + обновление статуса"""
        try:
            logger.info(f"Starting to process email ID: {email_log_id}")
            
            # 1. Подготавливаем данные для шаблона
            password_template = PasswordTemplateSchema(
                subject=self.settings.reset_password_template.subject,
                duration=email_request.duration,
                reset_link=email_request.reset_link,
                support_email=self.settings.support_email
            )

            email_body = await self.password_template_service.render_password_reset_template(password_template)

            # 3. Создаем объект для отправки
            email_to_send = EmailToSendSchema(
                id=email_log_id,
                to_email=email_request.to_email,
                body=email_body,
                subject=self.settings.reset_password_template.subject,
            )

            # 4. Отправляем письмо и обновляем статус
            await self.send_email_and_update_status(email_to_send)

        except Exception as e:
            logger.error(f"Exception while processing email ID: {email_log_id}. Error: {str(e)}")
            await self._update_email_status(email_log_id, EmailStatus.FAILED, str(e))

    async def send_email_and_update_status(self, email: EmailToSendSchema) -> None:
        """Отправляет письмо и обновляет статус в БД"""
        logger.info(f"Starting to send email ID: {email.id} to {email.to_email}")

        try:
            result = await self.sender.send_email(email)

            if result is True:
                logger.info(f"Email ID: {email.id} sent successfully")
                await self._update_email_status(email.id, EmailStatus.SENT)
            else:
                error_msg = str(result)
                logger.error(f"Failed to send email ID: {email.id}. Error: {error_msg}")
                await self._update_email_status(email.id, EmailStatus.FAILED, error_msg)

        except Exception as e:
            logger.error(f"Exception while sending email ID: {email.id}. Error: {str(e)}")
            await self._update_email_status(email.id, EmailStatus.FAILED, str(e))

    async def _update_email_status(self, email_id: uuid.UUID, status: EmailStatus, error: str | None = None) -> EmailLogReadSchema:
        """Обновляет статус email в БД"""
        logger.info(f"Updating email ID: {email_id} status to {status}")
        updated_log = await self.repository.update_status_and_error(email_id, status, error)
        logger.info(f"Email ID: {email_id} status updated successfully")
        return updated_log