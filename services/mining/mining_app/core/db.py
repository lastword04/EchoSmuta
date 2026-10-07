from asyncio import current_task
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID, uuid4

import psycopg  # <-- правильный импорт драйвера DB-API
from fastapi import Depends
from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from ..settings import settings

__all__ = (
    'AsyncSession',
    'AsyncSessionFactory',
    'Base',
    'Session',
    'SyncSessionFactory',
    'get_async_session',
)

POSTGRES_INDEXES_NAMING_CONVENTION = {
    'ix': '%(column_0_label)s_idx',
    'uq': '%(table_name)s_%(column_0_name)s_key',
    'ck': '%(table_name)s_%(constraint_name)s_check',
    'fk': '%(table_name)s_%(column_0_name)s_fkey',
    'pk': '%(table_name)s_pkey',
}

metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Асинхронный движок для FastAPI
asyncio_engine = create_async_engine(
    settings.db.dsn,
    connect_args={'server_settings': {'search_path': settings.db.scheme}},
    echo=False
)

# Синхронный движок для Celery
sync_engine = create_engine(
    settings.db.dsn_sync,
    module=psycopg,  # <-- передаём драйвер
    connect_args={'options': f'-c search_path={settings.db.scheme}'},
    echo=False,
    pool_pre_ping=True,
)

# Базовый асинхронный sessionmaker
_async_sessionmaker = async_sessionmaker(
    asyncio_engine,
    autocommit=False,
    expire_on_commit=False,
    future=True,
    autoflush=False,
)

# Scoped-фабрика для асинхронных сессий (для FastAPI и, возможно, других асинхронных контекстов)
AsyncSessionFactory = async_scoped_session(
    _async_sessionmaker,
    scopefunc=current_task
)

# Синхронная фабрика сессий (для Celery)
SyncSessionFactory = sessionmaker(
    sync_engine,
    autocommit=False,
    expire_on_commit=False,
    future=True,
    autoflush=False,
)

class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""
    metadata = metadata

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4 
    )

async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Генератор асинхронных сессий для FastAPI"""
    async with AsyncSessionFactory() as session:
        yield session

Session = Annotated[AsyncSession, Depends(get_async_session)]