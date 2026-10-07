import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.loggers import set_logging
from .core.redis import get_redis_client
from .settings import get_settings
from .middleware import apply_middleware
from .exceptions import apply_exceptions_handlers
from .router import apply_routes
from .apps.auth.depends import (
    get_redis_subscriber,
    get_token_service_factory,
    get_auth_character_event_handler,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Предварительная инициализация приложения.
    """
    set_logging()

    # Инициализация обработчика событий персонажей (бан -> инвалидация токенов)
    auth_event_handler = None
    try:
        settings = get_settings()
        redis_client = get_redis_client()
        redis_subscriber = get_redis_subscriber(redis_client)
        token_service_factory = get_token_service_factory(settings)
        auth_event_handler = get_auth_character_event_handler(redis_subscriber, token_service_factory)
        await auth_event_handler.start_listening()
        app.state.auth_event_handler = auth_event_handler
        logger.info("Auth character event handler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize auth character event handler: {e}")

    try:
        yield
    finally:
        if auth_event_handler is not None:
            await auth_event_handler.stop_listening()
            logger.info("Auth character event handler stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        docs_url='/docs',
        openapi_url='/docs.json',
    )

    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))

    return app