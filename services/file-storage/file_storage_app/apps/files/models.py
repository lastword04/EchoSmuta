import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, MappedColumn
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from shared.models import TimestampMixin
from typing import Optional
from ...core.db import Base


class File(Base, TimestampMixin):
    __tablename__ = "files"

    template_name: MappedColumn[Optional[str]] = mapped_column(sa.String(256), nullable=True, unique=True, index=True)
    path: MappedColumn[str] = mapped_column(sa.String(256), unique=True)
    creator_user_id: MappedColumn[uuid.UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    filename: MappedColumn[str] = mapped_column(sa.String(256), nullable=False)
    content_type: MappedColumn[str] = mapped_column(sa.String(256), nullable=False)
    size: MappedColumn[int] = mapped_column(sa.BigInteger, nullable=False)


