from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.loggers import set_logging
from .core.db import AsyncSessionFactory
from .middleware import apply_middleware
from .exceptions import apply_exceptions_handlers
from .router import apply_routes
from .initializator import initialize_app
import logging
import os
from sqlalchemy import text
from .settings import get_settings
from .apps.files.depends import get_file_service, get_s3_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Предварительная инициализация приложения.

    - устанавливаем настройки логгирования
    - устанавливаем настройки кеширования
    - устанавливаем настройки стриминга
    """
    set_logging()
    logger.warning(f"[WARMUP] file-storage worker start: pid={os.getpid()}")

    async with AsyncSessionFactory() as session:
        await initialize_app(session)
        await session.execute(text("SELECT 1"))  # прогрев пула БД

    # прогрев S3 до первого пользовательского запроса
    try:
        settings = get_settings()
        file_service = get_file_service(get_s3_client(settings), settings)
        await file_service.init()
    except Exception as e:
        logger.warning(f"S3 warmup failed, прогреется лениво на первом запросе: {e}")

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        docs_url='/docs',
        openapi_url='/docs.json',
    )

    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))

    return app