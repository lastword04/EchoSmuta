import logging
import uuid
from datetime import UTC

import redis
from redis.asyncio import Redis

from mining_app.apps.resources.repositories.character_resource_sync import (
    CharacterResourceSyncRepository,
)
from mining_app.settings import settings
from shared.services.templates import TextTemplateService

from ...core.celery import app as celery_app
from ...core.db import SyncSessionFactory
from ..resources.events.publisher import RedisPublisher
from ..resources.events.publisher_sync import RedisPublisherSync
from .adapters.characters_sync import CharacterServiceSyncClient
from .deals.use_cases.deals_sync import (
    CompleteDealSyncUseCase,
    ExpireDealSyncUseCase,
    RecoverCompletingDealsSyncUseCase,
)
from .events.items import ItemEvents
from .events.items_sync import ItemEventsSyncAdapter
from .repositories.character.character_items_sync import CharacterItemSyncRepository
from .repositories.crafting.character_start_creating_item_sync import (
    CharacterStartCreatingItemSyncRepository,
)
from .repositories.crafting.items_creating_action_sync import (
    ItemsCreatingActionSyncRepository,
)
from .repositories.items.experience_for_level_sync import (
    ItemExperienceForLevelSyncRepository,
)
from .repositories.items.items_component_sync import ItemComponentSyncRepository
from .repositories.items.items_sync import ItemSyncRepository
from .repositories.stats.character_city_trade_stats_sync import (
    CharacterCityTradeStatsSyncRepository,
)
from .services.adapters.item_templates import ItemTemplateService
from .services.crafting.items_creating_actions_sync import (
    ProcessItemsCreatingActionSyncService,
)
from .use_cases.cleanup_expired_items_sync import CleanupExpiredItemsSyncUseCase

logger = logging.getLogger(__name__)


# ===================== CRAFTING TASKS =====================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def finish_creating_task(self, action_id: uuid.UUID, character: dict, item_slug: str):
    logger.info(f"Starting crafting task: {action_id} for item {item_slug}")

    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)

        # Инициализация всех репозиториев
        items_creating_repo = ItemsCreatingActionSyncRepository(session)
        start_creating_repo = CharacterStartCreatingItemSyncRepository(session)
        item_repo = ItemSyncRepository(session)
        item_comp_repo = ItemComponentSyncRepository(session)
        char_resource_repo = CharacterResourceSyncRepository(session)
        char_item_repo = CharacterItemSyncRepository(session)
        
        # ✅ НОВОЕ: Репозитории для опыта
        char_city_trade_stats_repo = CharacterCityTradeStatsSyncRepository(session)
        item_experience_for_level_repo = ItemExperienceForLevelSyncRepository(session)

        character_service = CharacterServiceSyncClient()
        text_template_service = TextTemplateService(settings.system_messages_file_path)
        template_service = ItemTemplateService(text_template_service)

        # Создаём асинхронный Redis клиент для items_events
        redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        publisher = RedisPublisher(redis_client)
        items_events_async = ItemEvents(publisher)
        items_events_sync = ItemEventsSyncAdapter(items_events_async)

        # 👇 Создаём СИНХРОННЫЙ Redis клиент для economy_state_updated
        sync_redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        sync_publisher = RedisPublisherSync(sync_redis_client)

        service = ProcessItemsCreatingActionSyncService(
            repository=items_creating_repo,
            character_start_creating_repository=start_creating_repo,
            item_repository=item_repo,
            item_component_repository=item_comp_repo,
            character_resource_repository=char_resource_repo,
            character_item_repository=char_item_repo,
            character_service=character_service,
            character_city_trade_stats_repository=char_city_trade_stats_repo,
            item_experience_for_level_repository=item_experience_for_level_repo,
            template_service=template_service,
            items_events=items_events_sync,
            redis_publisher=sync_publisher,
            change_tiredness=settings.items_creating.change_tiredness,            
            chance_lose_resource=settings.items_creating.chance_lose_resource,
        )

        result = service.process_new_creating_action(action_id, character, item_slug)
        session.commit()
        logger.info(f"Process crafting completed: {result}")
        return result

    except Exception as e:
        session.rollback()
        logger.exception("Task failed")
        raise self.retry(exc=e)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def finish_continue_creating_task(self, action_id: uuid.UUID, character: dict, start_creating_id: uuid.UUID):
    logger.info(f"Starting continue crafting task: {action_id} for start_creating_id {start_creating_id}")

    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)

        items_creating_repo = ItemsCreatingActionSyncRepository(session)
        start_creating_repo = CharacterStartCreatingItemSyncRepository(session)
        item_repo = ItemSyncRepository(session)
        item_comp_repo = ItemComponentSyncRepository(session)
        char_resource_repo = CharacterResourceSyncRepository(session)
        char_item_repo = CharacterItemSyncRepository(session)
        
        # ✅ НОВОЕ: Репозитории для опыта
        char_city_trade_stats_repo = CharacterCityTradeStatsSyncRepository(session)
        item_experience_for_level_repo = ItemExperienceForLevelSyncRepository(session)

        character_service = CharacterServiceSyncClient()
        text_template_service = TextTemplateService(settings.system_messages_file_path)
        template_service = ItemTemplateService(text_template_service)

        # Создаём асинхронный Redis клиент для items_events
        redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        publisher = RedisPublisher(redis_client)
        items_events_async = ItemEvents(publisher)
        items_events_sync = ItemEventsSyncAdapter(items_events_async)

        # 👇 Создаём СИНХРОННЫЙ Redis клиент для economy_state_updated
        sync_redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        sync_publisher = RedisPublisherSync(sync_redis_client)

        service = ProcessItemsCreatingActionSyncService(
            repository=items_creating_repo,
            character_start_creating_repository=start_creating_repo,
            item_repository=item_repo,
            item_component_repository=item_comp_repo,
            character_resource_repository=char_resource_repo,
            character_item_repository=char_item_repo,
            character_service=character_service,
            character_city_trade_stats_repository=char_city_trade_stats_repo,
            item_experience_for_level_repository=item_experience_for_level_repo,
            template_service=template_service,
            items_events=items_events_sync,
            redis_publisher=sync_publisher,
            change_tiredness=settings.items_creating.change_tiredness,            
            chance_lose_resource=settings.items_creating.chance_lose_resource,
        )

        result = service.process_continue_creating_action(action_id, character, start_creating_id)
        session.commit()
        logger.info(f"Process continue crafting completed: {result}")
        return result

    except Exception as e:
        session.rollback()
        logger.exception("Task failed")
        raise self.retry(exc=e)
    finally:
        session.close()


# ===================== DEALS TASKS =====================

@celery_app.task(name="mining.expire_deals")
def expire_deals() -> int:
    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        
        # Создаём синхронный Redis publisher
        sync_redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        sync_publisher = RedisPublisherSync(sync_redis_client)
        
        character_service = CharacterServiceSyncClient()
        use_case = ExpireDealSyncUseCase(character_service, redis_publisher=sync_publisher)
        result = use_case(session, limit=50)
        logger.info(f"Expire deals completed: {result}")
        return result
    except Exception:
        logger.exception("Expire deals failed")
        raise
    finally:
        session.close()


@celery_app.task(name="mining.recover_completing_deals")
def recover_completing_deals() -> int:
    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        
        # Создаём синхронный Redis publisher
        sync_redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        sync_publisher = RedisPublisherSync(sync_redis_client)
        
        character_service = CharacterServiceSyncClient()
        complete_use_case = CompleteDealSyncUseCase(character_service, redis_publisher=sync_publisher)
        use_case = RecoverCompletingDealsSyncUseCase(complete_use_case)
        result = use_case(session, limit=50)
        logger.info(f"Recover completing deals completed: {result}")
        return result
    except Exception:
        logger.exception("Recover completing deals failed")
        raise
    finally:
        session.close()

    


@celery_app.task(name="mining.cleanup_expired_items")
def cleanup_expired_items() -> int:
    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        
        # Инициализация зависимостей
        redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        publisher = RedisPublisher(redis_client)
        items_events_async = ItemEvents(publisher)
        items_events_sync = ItemEventsSyncAdapter(items_events_async)
        
        text_template_service = TextTemplateService(settings.system_messages_file_path)
        template_service = ItemTemplateService(text_template_service)
        
        use_case = CleanupExpiredItemsSyncUseCase(
            items_events=items_events_sync,
            template_service=template_service,
        )
        
        result = use_case(session, limit=100)
        logger.info(f"Cleanup expired items completed: {result} items deleted")
        return result
    except Exception:
        logger.exception("Cleanup expired items failed")
        raise
    finally:
        session.close()



# ===================== SALE HISTORY TASKS =====================

@celery_app.task(name="mining.cleanup_sale_history")
def cleanup_sale_history(days: int = 180) -> int:
    """Удаляет записи из sale_history старше N дней (полгода по умолчанию)."""
    from datetime import datetime, timedelta

    from sqlalchemy import delete

    from .models import SaleHistory

    session = SyncSessionFactory()
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = session.execute(
            delete(SaleHistory).where(SaleHistory.created_at < cutoff)
        )
        session.commit()
        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} old sale_history records (older than {days} days)")
        return deleted
    except Exception:
        session.rollback()
        logger.exception("Cleanup sale history failed")
        raise
    finally:
        session.close()