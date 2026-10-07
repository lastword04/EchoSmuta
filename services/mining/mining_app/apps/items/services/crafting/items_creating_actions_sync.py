import logging
import random
import uuid
from datetime import UTC, datetime

from ....resources.events.publisher import RedisPublisherProtocol
from ....resources.repositories.character_resource_sync import (
    CharacterResourceSyncRepository,
)
from ...adapters.characters_sync import CharacterServiceSyncClient
from ...enums import ItemCreatingStatus
from ...repositories.character.character_items_sync import CharacterItemSyncRepository
from ...repositories.crafting.character_start_creating_item_sync import (
    CharacterStartCreatingItemSyncRepository,
)
from ...repositories.crafting.items_creating_action_sync import (
    ItemsCreatingActionSyncRepository,
)
from ...repositories.items.experience_for_level_sync import (
    ItemExperienceForLevelSyncRepository,
)
from ...repositories.items.items_component_sync import ItemComponentSyncRepository
from ...repositories.items.items_sync import ItemSyncRepository
from ...repositories.stats.character_city_trade_stats_sync import (
    CharacterCityTradeStatsSyncRepository,
)
from ...services.adapters.item_templates import ItemTemplateService
from .processors_sync import (
    CraftingResultProcessorSync,
    CraftingResultProcessorSyncProtocol,
)

logger = logging.getLogger(__name__)

class ProcessItemsCreatingActionSyncService:
    def __init__(
        self,
        repository: ItemsCreatingActionSyncRepository,
        character_start_creating_repository: CharacterStartCreatingItemSyncRepository,
        item_repository: ItemSyncRepository,
        item_component_repository: ItemComponentSyncRepository,
        character_resource_repository: CharacterResourceSyncRepository,
        character_item_repository: CharacterItemSyncRepository,
        character_service: CharacterServiceSyncClient,
        character_city_trade_stats_repository: CharacterCityTradeStatsSyncRepository,
        item_experience_for_level_repository: ItemExperienceForLevelSyncRepository,
        template_service: ItemTemplateService,
        items_events,
        redis_publisher: RedisPublisherProtocol | None = None,
        change_tiredness: float = 0.03,
        chance_lose_resource: float = 0.2,
        processor: CraftingResultProcessorSyncProtocol | None = None,
    ):
        self.repository = repository
        self.character_start_creating_repository = character_start_creating_repository
        self.item_repository = item_repository
        self.item_component_repository = item_component_repository
        self.character_resource_repository = character_resource_repository
        self.character_item_repository = character_item_repository
        self.character_service = character_service
        self.character_city_trade_stats_repository = character_city_trade_stats_repository
        self.item_experience_for_level_repository = item_experience_for_level_repository
        self.template_service = template_service
        self.items_events = items_events
        self.redis_publisher = redis_publisher
        self.change_tiredness = change_tiredness
        self.chance_lose_resource = chance_lose_resource
        # Обработка исхода стадии вынесена в CraftingResultProcessorSync.
        # Валидация (уровень/усталость/локация/лицензия/ресурсы) в воркере НЕ
        # выполняется: она уже пройдена на старте крафта в async-сервисе.
        self.processor = processor or CraftingResultProcessorSync(
            repository=repository,
            character_start_creating_repository=character_start_creating_repository,
            character_item_repository=character_item_repository,
            character_resource_repository=character_resource_repository,
            character_service=character_service,
            character_city_trade_stats_repository=character_city_trade_stats_repository,
            item_experience_for_level_repository=item_experience_for_level_repository,
            template_service=template_service,
            items_events=items_events,
            redis_publisher=redis_publisher,
            change_tiredness=change_tiredness,
            chance_lose_resource=chance_lose_resource,
        )

    def process_new_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        item_slug: str,
    ) -> dict:
        logger.info("Processing NEW item crafting action: action_id=%s", action_id)
        character_id = uuid.UUID(character_data["id"])

        creating_action = self.repository.get_for_character(action_id, character_id)
        if not creating_action:
            return {"status": "missing"}

        if creating_action.status != ItemCreatingStatus.IN_PROGRESS:
            return {"status": "already_processed"}

        now = datetime.now(UTC)
        if creating_action.finish_time > now:
            remaining = (creating_action.finish_time - now).total_seconds()
            if remaining > 1:
                return {"status": "rescheduled", "remaining": int(remaining)}

        item = self.item_repository.get_by_slug(item_slug)
        components = self.item_component_repository.get_components_with_resource_names(item_slug)

        character_stats = self.character_city_trade_stats_repository.get_or_create(
            character_id=character_id, location_slug=creating_action.location_slug
        )
        experience_level_data = self.item_experience_for_level_repository.get_current_level(character_stats.level)
        chance_creating = experience_level_data.success_rate_one

        success_roll = random.random()

        # Исход стадии применяет CraftingResultProcessorSync (формулы и порядок
        # коммитов сохранены 1:1); валидация в воркере не выполняется
        return self.processor.process(
            creating_action=creating_action,
            item=item,
            components=components,
            item_slug=item_slug,
            character_id=character_id,
            success_rate=chance_creating,
            success_roll=success_roll,
            is_final_stage=False,
            new_stage=1,
        )

    def process_continue_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        start_creating_id: uuid.UUID,
    ) -> dict:
        logger.info("Processing CONTINUE item crafting action: action_id=%s", action_id)
        character_id = uuid.UUID(character_data["id"])

        creating_action = self.repository.get_for_character(action_id, character_id)
        if not creating_action:
            return {"status": "missing"}

        if creating_action.status != ItemCreatingStatus.IN_PROGRESS:
            return {"status": "already_processed"}

        now = datetime.now(UTC)
        if creating_action.finish_time > now:
            remaining = (creating_action.finish_time - now).total_seconds()
            if remaining > 1:
                return {"status": "rescheduled", "remaining": int(remaining)}

        start_creating = self.character_start_creating_repository.get(start_creating_id)
        item = self.item_repository.get_by_slug(start_creating.item_slug)
        components = self.item_component_repository.get_components_with_resource_names(start_creating.item_slug)

        current_stage = creating_action.craft_stage
        is_final_stage = (current_stage + 1) >= (item.craft_stages or 1)

        character_stats = self.character_city_trade_stats_repository.get_or_create(
            character_id=character_id, location_slug=creating_action.location_slug
        )
        experience_level_data = self.item_experience_for_level_repository.get_current_level(character_stats.level)
        chance_creating = experience_level_data.success_rate_one

        success_roll = random.random()

        # Исход стадии применяет CraftingResultProcessorSync (списание ресурсов,
        # выдача предмета, опыт, усталость, события) — формулы сохранены 1:1
        return self.processor.process(
            creating_action=creating_action,
            item=item,
            components=components,
            item_slug=start_creating.item_slug,
            character_id=character_id,
            success_rate=chance_creating,
            success_roll=success_roll,
            is_final_stage=is_final_stage,
            new_stage=current_stage + 1,
            start_creating_id=start_creating_id,
        )
