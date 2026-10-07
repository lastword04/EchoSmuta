import uuid
import sqlalchemy as sa
from shared.schemas.email import EmailStatus, EmailLogReadSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException
from ..models import EmailLog
from ..schemas import EmailLogCreateSchema, EmailLogUpdateSchema


class EmailLogRepositoryProtocol(BaseRepositoryImpl[
    EmailLog,
    EmailLogReadSchema,
    EmailLogCreateSchema,
    EmailLogUpdateSchema
]):
    async def update_status_and_error(
        self, email_log_id: uuid.UUID, status: EmailStatus, error: str | None = None
    ) -> EmailLogReadSchema:
        """
        Update the status and error of an email log entry.
        
        :param email_log_id: The ID of the email log to update.
        :param status: The new status of the email log.
        :param error: Optional error message if the email sending failed.
        :return: Updated EmailLogReadSchema instance.
        """


class EmailLogRepository(EmailLogRepositoryProtocol):
    async def update_status_and_error(
        self, email_log_id: uuid.UUID, status: EmailStatus, error: str | None = None
    ) -> EmailLogReadSchema:
        query = (
            sa.update(self.model_type)
            .where(self.model_type.id == email_log_id)
            .values(status=status, error=error)
            .returning(self.model_type)
        )
        result = await self.session.execute(query)
        updated_email_log = result.scalar_one_or_none()
        
        if updated_email_log is None:
            raise ModelNotFoundException(model=self.model_type, model_id=email_log_id)
        
        return self.read_schema_type.model_validate(updated_email_log, from_attributes=True)