from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from .core.loggers import set_logging
from .core.redis import get_redis_client
from .settings import settings
from .middleware import apply_middleware
from .exceptions import apply_exceptions_handlers
from .router import apply_routes
from .apps.messages.depends import (
    get_send_and_publish_message_service_factory,
    get_visibility_service_factory,
    get_character_handler,
    get_items_handler,
    get_deals_handler,
    get_house_handler,
    get_rest_handler,
    get_mining_handler,
    get_monster_attack_handler,
    get_redis_subscriber,
    get_redis_publisher,
    init_text_template_service,
    get_text_template_service,
)
from .apps.messages.depends_shared import get_character_adapter
from .apps.messages.events.character_presence_handler import CharacterPresenceHandler

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Предварительная инициализация приложения.
    """
    set_logging()

    init_text_template_service(settings.system_messages_file_path)
    logger.info("Text template service initialized successfully")

    # Создаем сессию БД для инициализации сервисов
    try:
        # Фабрики
        message_service_factory = get_send_and_publish_message_service_factory()
        visibility_service_factory = get_visibility_service_factory()
        template_service = get_text_template_service()

        # Подписчики
        redis_client = get_redis_client()
        redis_subscriber = get_redis_subscriber(redis_client)
        mining_redis_subscriber = get_redis_subscriber(redis_client)
        items_redis_subscriber = get_redis_subscriber(redis_client)

        # ← ДОБАВИТЬ: Создаем character adapter для handlers
        character_adapter = get_character_adapter(settings)

        # Инициализируем репозитории и сервисы
        character_event_handler = get_character_handler(
            redis_subscriber=redis_subscriber,
            redis_publisher=get_redis_publisher(get_redis_client()), 
            template_service=template_service,
            message_service_factory=message_service_factory,
            visibility_service_factory=visibility_service_factory
        )
        # Создаем обработчик событий
        await character_event_handler.start_listening()
        
        # Сохраняем в state приложения
        app.state.character_event_handler = character_event_handler
        
        logger.info("Character event handler initialized successfully")
        
        mining_event_handler = get_mining_handler(
                mining_redis_subscriber,
                message_service_factory,
                template_service
        )
        await mining_event_handler.start_listening()
        app.state.mining_event_handler = mining_event_handler
        logger.info("Mining event handler initialized successfully")

        # ← ИЗМЕНИТЬ: Передаем character_adapter как третий параметр
        items_event_handler = get_items_handler(
            items_redis_subscriber,
            message_service_factory,
            character_adapter,  # ← ДОБАВИТЬ
        )
        await items_event_handler.start_listening()
        app.state.items_event_handler = items_event_handler
        logger.info("Items event handler initialized successfully")
        
        # Создаём отдельный subscriber и publisher для deals
        deals_redis_subscriber = get_redis_subscriber(redis_client)
        deals_redis_publisher = get_redis_publisher(redis_client)
        
        # Инициализируем обработчик сделок
        deals_event_handler = get_deals_handler(
            deals_redis_subscriber,
            deals_redis_publisher,
            message_service_factory,
            template_service,
        )
        await deals_event_handler.start_listening()
        app.state.deals_event_handler = deals_event_handler
        logger.info("Deals event handler initialized successfully")

        # House events handler
        house_redis_subscriber = get_redis_subscriber(redis_client)
        house_redis_publisher = get_redis_publisher(redis_client)
        
        house_event_handler = get_house_handler(
            house_redis_subscriber,
            house_redis_publisher,
        )
        await house_event_handler.start_listening()
        app.state.house_event_handler = house_event_handler
        logger.info("House event handler initialized successfully")

        # Rest events handler (номера в гостинице)
        rest_redis_subscriber = get_redis_subscriber(redis_client)
        rest_redis_publisher = get_redis_publisher(redis_client)
        rest_event_handler = get_rest_handler(
            rest_redis_subscriber,
            rest_redis_publisher,
        )
        await rest_event_handler.start_listening()
        app.state.rest_event_handler = rest_event_handler
        logger.info("Rest event handler initialized successfully")

        # Character presence handler (online/offline + change_location)
        presence_subscriber1 = get_redis_subscriber(redis_client)
        presence_subscriber2 = get_redis_subscriber(redis_client)
        presence_publisher = get_redis_publisher(redis_client)
        presence_handler = CharacterPresenceHandler(presence_subscriber1, presence_subscriber2, presence_publisher)
        await presence_handler.start_listening()
        app.state.presence_handler = presence_handler

        # monster_event_handler = get_monster_attack_handler(
        #     monster_redis_subscriber,
        #     message_service_factory,
        #     template_service
        # )
        # await monster_event_handler.start_listening()
        # app.state.monster_event_handler = monster_event_handler
        # logger.info("Monster event handler initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize character event handler: {e}")
        yield  # Все равно запускаем приложение, даже если обработчик событий не работает
    finally:
        # Cleanup
        if hasattr(app.state, 'character_event_handler'):
            await app.state.character_event_handler.stop_listening()
        if hasattr(app.state, 'mining_event_handler'):
            await app.state.mining_event_handler.stop_listening()
        if hasattr(app.state, 'items_event_handler'):
            await app.state.items_event_handler.stop_listening()
        if hasattr(app.state, 'deals_event_handler'):
            await app.state.deals_event_handler.stop_listening()
        if hasattr(app.state, 'house_event_handler'):
            await app.state.house_event_handler.stop_listening()
        if hasattr(app.state, 'rest_event_handler'):
            await app.state.rest_event_handler.stop_listening()
        if hasattr(app.state, 'presence_handler'):
            await app.state.presence_handler.stop_listening()
        # if hasattr(app.state, 'monster_event_handler'):
        #     await app.state.monster_event_handler.stop_listening()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        docs_url='/docs',
        openapi_url='/docs.json',
    )

    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))

    return app