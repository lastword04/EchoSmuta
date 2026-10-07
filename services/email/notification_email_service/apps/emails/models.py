import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from shared.schemas.email import EmailStatus
from ...core.db import Base
from shared.models import TimestampMixin

class EmailLog(Base, TimestampMixin):
    __tablename__ = 'email_logs'

    to_email: Mapped[str] = mapped_column(sa.String, nullable=False)
    template_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    status: Mapped[EmailStatus] = mapped_column(sa.Enum(EmailStatus), nullable=False)
    error: Mapped[str] = mapped_column(sa.Text, nullable=True)