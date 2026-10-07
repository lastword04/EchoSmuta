from fastapi import Depends
import redis.asyncio as redis
from ....core.redis import get_redis_client
from ....settings import Settings, get_settings
from ...notebook.depends import get_notebook_service
from ...notebook.services.notebook import NotebookCRUServiceProtocol
from ...panels.depends import get_item_service
from ...panels.services.panels import ItemsCRUServiceProtocol
from ...stats.depends import get_modifiers_collector
from ...stats.services.effective_stats import EffectiveStatsService
from ...stats.services.collector.modifiers import ModifiersCollector
from ..adapters.chats import ChatSettingsServiceClientProtocol, ChatSettingsServiceClient
from ..adapters.files import FileServiceClientProtocol, FileServiceClient
from ..adapters.notebook import CreateNotebookAdapterProtocol, CreateNotebookAdapter
from ..adapters.panels import CreateItemsAdapterProtocol, CreateItemsAdapter
from ..adapters.category import CategoryServiceClientProtocol, CategoryServiceClient
from ..adapters.mining import MiningServiceClientProtocol, MiningServiceClient
from ..events.publisher import RedisPublisher, RedisPublisherProtocol
from ..events.characters import CharacterEvents, CharacterEventsProtocol


def get_redis_publisher(redis: redis.Redis = Depends(get_redis_client)) -> RedisPublisherProtocol:
    return RedisPublisher(redis)


def get_file_client(settings: Settings = Depends(get_settings)) -> FileServiceClientProtocol:
    return FileServiceClient(base_url=settings.file_service_app.base_url)


def get_notebook_adapter(notebook_service: NotebookCRUServiceProtocol = Depends(get_notebook_service)) -> CreateNotebookAdapterProtocol:
    return CreateNotebookAdapter(notebook_service=notebook_service)


def get_items_adapter(items_service: ItemsCRUServiceProtocol = Depends(get_item_service)) -> CreateItemsAdapterProtocol:
    return CreateItemsAdapter(items_service)


def get_chat_settings_client(settings: Settings = Depends(get_settings)) -> ChatSettingsServiceClientProtocol:
    return ChatSettingsServiceClient(base_url=settings.chat_service_app.base_url)


def get_category_stats_adapter(settings: Settings = Depends(get_settings)) -> CategoryServiceClientProtocol:
    return CategoryServiceClient(base_url=settings.category_service_app.base_url)


def get_mining_adapter(settings: Settings = Depends(get_settings)) -> MiningServiceClientProtocol:
    """Функция для получения adapter для Mining сервиса."""
    return MiningServiceClient(
        base_url=settings.mining_service_app.base_url,
        permissions=["mining:read", "mining:write"],
    )


def get_effective_stats_service(
    modifiers_collector: ModifiersCollector = Depends(get_modifiers_collector),
) -> EffectiveStatsService:
    return EffectiveStatsService(modifiers_collector=modifiers_collector)


def get_character_events(publisher: RedisPublisherProtocol = Depends(get_redis_publisher)) -> CharacterEventsProtocol:
    """Создаёт CharacterEvents с Redis publisher"""
    return CharacterEvents(publisher)
