from typing import Annotated, AsyncGenerator
from uuid import uuid4, UUID
from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from ..settings import settings

__all__ = (
    "Base",
    "Session",
    "AsyncSession",
    "get_async_session",
)

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

asyncio_engine = create_async_engine(
    settings.db.dsn,
    connect_args={"server_settings": {"search_path": settings.db.scheme}},
    echo=settings.debug,
)

AsyncSessionFactory = async_sessionmaker(
    asyncio_engine,
    autocommit=False,
    expire_on_commit=False,
    future=True,
    autoflush=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""

    metadata = metadata

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронных сессий для FastAPI"""
    async with AsyncSessionFactory() as session:
        # logger.debug(f"ASYNC Pool: {asyncio_engine.pool.status()}")
        yield session


Session = Annotated[AsyncSession, Depends(get_async_session)]
