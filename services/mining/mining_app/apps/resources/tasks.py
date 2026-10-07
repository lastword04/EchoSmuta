import logging
import uuid

import redis  # Синхронный redis

from mining_app.settings import settings
from shared.services.templates import TextTemplateService

from ...core.celery import app as celery_app
from ...core.db import SyncSessionFactory
from .adapters.characters_sync import CharacterServiceSyncClient
from .events.mining_sync import MiningEventsSync
from .events.monster_sync import MonsterEventsSync
from .events.publisher_sync import RedisPublisherSync
from .repositories.character_resource_sync import CharacterResourceSyncRepository
from .repositories.experience_for_level_sync import ExperienceForLevelSyncRepository
from .repositories.location_character_expierence_sync import CharacterLocationStatsSyncRepository
from .repositories.location_resources_character_sync import LocationResourcesCharacterSyncRepository
from .repositories.location_resources_sync import LocationResourceSyncRepository
from .repositories.location_settings_sync import LocationSettingsSyncRepository
from .repositories.mining_actions_sync import MiningActionSyncRepository
from .repositories.monsters_location_sync import MonsterLocationSyncRepository
from .services.character_resource_sync import CharacterResourceSyncService
from .services.experience_for_level_sync import ExperienceForLevelSyncService
from .services.location_resources_sync import LocationResourceSyncService
from .services.location_settings_sync import LocationSettingsSyncService
from .services.mining_actions_sync import ProcessMiningActionSyncService
from .services.mining_templates import MiningTemplateService
from .services.monster_location_sync import MonsterLocationSyncService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def finish_mining_task(self, action_id: uuid.UUID, character: dict):
    logger.info(f"Starting mining task: {action_id}")
    
    session = SyncSessionFactory()
    character_service = None
    redis_publisher = None
    
    try:
        celery_app.connection().ensure_connection(max_retries=3)

        # 1. Создаём sync Redis publisher
        redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
        redis_publisher = RedisPublisherSync(redis_client)
        mining_events = MiningEventsSync(redis_publisher)
        monster_events = MonsterEventsSync(redis_publisher)

        # 2. Создаём sync repositories
        mining_repo = MiningActionSyncRepository(session)
        experience_repo = ExperienceForLevelSyncRepository(session)
        location_settings_repo = LocationSettingsSyncRepository(session)
        location_resource_repo = LocationResourceSyncRepository(session)
        location_resources_char_repo = LocationResourcesCharacterSyncRepository(session)
        location_char_exp_repo = CharacterLocationStatsSyncRepository(session)
        character_resource_repo = CharacterResourceSyncRepository(session)
        monster_repo = MonsterLocationSyncRepository(session)

        # 3. Создаём sync services
        experience_service = ExperienceForLevelSyncService(experience_repo)
        location_settings_service = LocationSettingsSyncService(location_settings_repo)
        location_resource_service = LocationResourceSyncService(location_resource_repo)
        character_resource_service = CharacterResourceSyncService(character_resource_repo)
        monster_service = MonsterLocationSyncService(monster_repo)

        # 4. Создаём template service
        text_template_service = TextTemplateService(settings.system_messages_file_path)
        template_service = MiningTemplateService(text_template_service)

        # 5. Создаём sync character client
        character_service = CharacterServiceSyncClient()

        # 6. Собираем ProcessMiningActionSyncService
        service = ProcessMiningActionSyncService(
            repository=mining_repo,
            experience_service=experience_service,
            location_settings_service=location_settings_service,
            location_resource_service=location_resource_service,
            location_resources_character_repository=location_resources_char_repo,
            location_character_experience_repository=location_char_exp_repo,
            character_resource_service=character_resource_service,
            mining_events=mining_events,
            monster_events=monster_events,
            character_service=character_service,
            monster_service=monster_service,
            template_service=template_service,
            redis_publisher=redis_publisher,
            change_tiredness=settings.mining.change_tiredness,
            min_attack_monster_health_percentage=settings.mining.min_attack_monster_health_percentage,
            min_attack_monster_tiredness=settings.mining.min_attack_monster_tiredness,
            default_monster_attack_chance=settings.mining.default_monster_attack_chance,
            default_attack_monster_standart=settings.mining.default_attack_monster_standart
        )

        # 7. Выполняем
        result = service.process_mining_action(action_id, character)
        
        session.commit()
        logger.info(f"Process mining completed: {result}")
        return result

    except Exception as e:
        session.rollback()
        logger.exception("Task failed")
        raise self.retry(exc=e)
    finally:
        session.close()
        if character_service:
            character_service.close()
        if redis_publisher:
            redis_publisher.close()