import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .apps.items.deps.crafting import get_cancel_crafting_actions_factory, get_crafting_handler
from .apps.items.deps.deals import get_cancel_deal_actions_factory
from .apps.items.events.handlers.deal_auto_cancel_handler import DealAutoCancelHandler
from .apps.resources.depends import (
    get_cancel_mining_actions_factory,
    get_mining_handler,
    get_redis_client,
    get_redis_subscriber,
    init_text_template_service,
)
from .core.db import AsyncSessionFactory
from .core.loggers import set_logging
from .exceptions import apply_exceptions_handlers
from .initializator import initialize_app
from .middleware import apply_middleware
from .router import apply_routes
from .settings import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    set_logging()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    init_text_template_service(settings.system_messages_file_path)
    logger.info("Text template service initialized successfully")

    async with AsyncSessionFactory() as session:
        await initialize_app(session)

    try:
        redis_client = get_redis_client()
        
        # 🛡️ ИСПРАВЛЕНИЕ: Создаем ОТДЕЛЬНЫЕ экземпляры сабскрайбера для каждого хендлера,
        # чтобы избежать конфликта при чтении из одного pubsub.listen()
        mining_redis_subscriber = get_redis_subscriber(redis_client)
        crafting_redis_subscriber = get_redis_subscriber(redis_client)
        deal_redis_subscriber = get_redis_subscriber(redis_client) 

        # === MINING EVENT HANDLER ===
        mining_service_factory = get_cancel_mining_actions_factory()
        mining_event_handler = get_mining_handler(
            redis_subscriber=mining_redis_subscriber,
            cancel_mining_service_factory=mining_service_factory
        )
        await mining_event_handler.start_listening()
        app.state.mining_event_handler = mining_event_handler
        logger.info("Mining event handler initialized successfully")

        # === CRAFTING EVENT HANDLER ===
        crafting_service_factory = get_cancel_crafting_actions_factory()
        crafting_event_handler = get_crafting_handler(
            redis_subscriber=crafting_redis_subscriber,
            cancel_crafting_service_factory=crafting_service_factory
        )
        await crafting_event_handler.start_listening()
        app.state.crafting_event_handler = crafting_event_handler
        logger.info("Crafting event handler initialized successfully")

        # === 🛡️ DEAL AUTO-CANCEL EVENT HANDLER ===
        deal_cancel_factory = get_cancel_deal_actions_factory()
        
        deal_auto_cancel_handler = DealAutoCancelHandler(
            redis_subscriber=deal_redis_subscriber,
            cancel_deal_factory=deal_cancel_factory,
            session_factory=AsyncSessionFactory, 
        )
        await deal_auto_cancel_handler.start_listening()
        app.state.deal_auto_cancel_handler = deal_auto_cancel_handler
        logger.info("Deal auto-cancel event handler initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize event handlers: {e}")
        yield
    finally:
        # Cleanup
        if hasattr(app.state, 'mining_event_handler'):
            await app.state.mining_event_handler.stop_listening()
        if hasattr(app.state, 'crafting_event_handler'):
            await app.state.crafting_event_handler.stop_listening()
        if hasattr(app.state, 'deal_auto_cancel_handler'):
            await app.state.deal_auto_cancel_handler.stop_listening()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        docs_url='/docs',
        openapi_url='/docs.json',
    )
    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))
    return app