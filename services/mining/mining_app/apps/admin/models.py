import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.models import CreationTimeMixin

from ...core.db import Base


class AdminLog(Base, CreationTimeMixin):
    __tablename__ = "admin_logs"

    admin_user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
