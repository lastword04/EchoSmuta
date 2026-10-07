import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.loggers import set_logging
from .core.db import AsyncSessionFactory
from .middleware import apply_middleware
from .exceptions import apply_exceptions_handlers
from .router import apply_routes
from .initializator import initialize_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Предварительная инициализация приложения.

    - устанавливаем настройки логгирования
    - устанавливаем настройки кеширования
    - устанавливаем настройки стриминга
    """
    set_logging()


    async with AsyncSessionFactory() as session:
        # Инициализация базы данных
        await initialize_app(session)
    # stream_repository = await get_streaming_repository_type()
    # await stream_repository.start(settings.kafka)

    yield

    # await stream_repository.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        docs_url='/docs',
        openapi_url='/docs.json',
    )

    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))

    return app