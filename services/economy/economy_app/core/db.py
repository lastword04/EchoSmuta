import asyncio
import sys
from typing import Annotated, AsyncGenerator
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..settings import settings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

metadata = MetaData(naming_convention={
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
})
asyncio_engine = create_async_engine(settings.db.dsn, connect_args={"server_settings": {"search_path": settings.db.scheme}}, echo=settings.debug)
AsyncSessionFactory = async_sessionmaker(asyncio_engine, expire_on_commit=False, autoflush=False)


class Base(AsyncAttrs, DeclarativeBase):
    metadata = metadata
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_async_session)]
