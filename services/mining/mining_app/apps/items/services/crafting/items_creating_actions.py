import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

from celery.result import AsyncResult

from shared.exceptions import PermissionDeniedError
from shared.schemas.captcha import CaptchaVerificationRequest

from ....resources.events.publisher import RedisPublisherProtocol
from ....resources.services.character_resource import CharacterResourceServiceProtocol
from ...adapters.captcha import CaptchaServiceClientProtocol
from ...adapters.characters import CharacterServiceClientProtocol
from ...enums import ItemCreatingStatus
from ...events.items import ItemEventsProtocol
from ...exceptions import (
    ItemAlreadyCreatingError,
    ItemCraftAlreadyStartedError,
    RecipeNotFoundError,
)
from ...repositories.building.building import BuildingRepositoryProtocol
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.crafting.character_start_creating_item import (
    CharacterStartCreatingItemRepositoryProtocol,
)
from ...repositories.crafting.items_creating_action import (
    ItemsCreatingActionRepositoryProtocol,
)
from ...repositories.recipes.character_recipes import CharacterRecipesRepositoryProtocol
from ...repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepositoryProtocol,
)
from ...schemas import (
    CharacterStartCreatingItemCreateSchema,
    ItemsCreatingActionCreateSchema,
    ItemsCreatingActionReadSchema,
    ItemsCreatingActionResponseSchema,
)
from ...services.adapters.item_templates import ItemTemplateServiceProtocol
from ...services.crafting_license.crafting_license import CraftingLicenseServiceProtocol
from ...services.items.experience_for_level import ItemExperienceForLevelServiceProtocol
from ...services.items.items import ItemServiceProtocol
from ...services.items.items_component import ItemComponentServiceProtocol
from .processors import CraftingResultProcessor, CraftingResultProcessorProtocol

# Re-export для тестов (test_create_items_creating_action.py импортирует отсюда)
from .validators import (
    PRODUCTION_LOCATION_SLUGS,  # noqa: F401
    CraftingValidator,
    CraftingValidatorProtocol,
)

logger = logging.getLogger(__name__)


class ItemsCreatingActionServiceProtocol(Protocol):
    async def get_processing_creating_action(self, character_id: uuid.UUID) -> ItemsCreatingActionResponseSchema:
        ...

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        ...

    async def exists_processing_creating_action(self, character_id: uuid.UUID) -> bool:
        ...

    async def cancel_expired_actions(
        self,
        character_id: uuid.UUID,
        older_than_minutes: int | None = None,
    ) -> int:
        ...


class ItemsCreatingActionService(ItemsCreatingActionServiceProtocol):
    def __init__(
        self,
        repository: ItemsCreatingActionRepositoryProtocol
    ):
        self.repository = repository

    async def get_processing_creating_action(self, character_id: uuid.UUID) -> ItemsCreatingActionResponseSchema:
        action = await self.repository.get_processing_creating_action(character_id)
        if action is None:
            return ItemsCreatingActionResponseSchema(
                status=ItemCreatingStatus.DONE,
                location_slug=None
            )
        return ItemsCreatingActionResponseSchema(
            id=action.id,
            status=action.status,
            location_slug=action.location_slug,
            message=action.message,
            remaining_time_seconds=int((action.finish_time - datetime.now(UTC)).total_seconds()),
            finish_time=action.finish_time
        )

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        return await self.repository.get_for_character(action_id, character_id)

    async def exists_processing_creating_action(self, character_id: uuid.UUID) -> bool:
        return await self.repository.exists_processing_creating_action(character_id)

    async def cancel_expired_actions(
        self,
        character_id: uuid.UUID,
        older_than_minutes: int | None = None,
    ) -> int:
        return await self.repository.cancel_expired_for_character(
            character_id, older_than_minutes=older_than_minutes
        )


class CancelItemsCreatingProcessServiceProtocol(Protocol):
    async def cancel_creating(self, character_id: uuid.UUID) -> bool:
        ...


class CancelItemsCreatingProcessService(CancelItemsCreatingProcessServiceProtocol):
    def __init__(self, repository: ItemsCreatingActionRepositoryProtocol):
        self.repository = repository

    async def cancel_creating(self, character_id: uuid.UUID) -> bool:
        creating = await self.repository.get_processing_creating_action(character_id)
        if not creating:
            logger.warning("No active creating action found for character %s", character_id)
            return False

        # Пытаемся отменить Celery-задачу (best effort)
        if creating.celery_task_id:
            try:
                from .....core.celery_app import celery_app

                task_result = AsyncResult(creating.celery_task_id, app=celery_app)
                if task_result.state in ["PENDING", "RECEIVED", "STARTED"]:
                    task_result.revoke(terminate=True, signal='SIGTERM')
                    logger.info("Celery task %s revoked for character %s",
                                creating.celery_task_id, character_id)
                else:
                    logger.info("Celery task %s in state %s, skip revoke",
                                creating.celery_task_id, task_result.state)
            except Exception as e:
                logger.error("Failed to revoke Celery task %s: %s", creating.celery_task_id, str(e))

        # ВСЕГДА отменяем запись в БД
        await self.repository.cancel_creating(creating.id)
        logger.info("Creating action %s cancelled for character %s", creating.id, character_id)
        return True


class CreateItemsCreatingActionServiceProtocol(Protocol):
    async def create_new_item_crafting_action(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        """Создать действие крафта для нового предмета (craft_stage=0)"""
        ...
    
    async def continue_item_crafting_action(
        self,
        character_id: uuid.UUID,
        start_creating_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        """Продолжить крафт существующего предмета (craft_stage > 0)"""
        ...


class CreateItemsCreatingActionService(CreateItemsCreatingActionServiceProtocol):
    def __init__(
        self,
        repository: ItemsCreatingActionRepositoryProtocol,
        character_service: CharacterServiceClientProtocol,
        building_repository: BuildingRepositoryProtocol,
        item_service: ItemServiceProtocol,
        character_resource_service: CharacterResourceServiceProtocol,
        item_component_service: ItemComponentServiceProtocol,
        city_trading_shop_repository: 'CityTradingShopCharacterRepositoryProtocol',
        character_recipes_repository: CharacterRecipesRepositoryProtocol,
        character_start_creating_repository: CharacterStartCreatingItemRepositoryProtocol,
        captcha_adapter: CaptchaServiceClientProtocol,
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
        cooldown_seconds: int = 180,
        crafting_license_service: CraftingLicenseServiceProtocol | None = None,
        min_valid_level: int = 3,      
        max_valid_tiredness: float = 0.495,
        validator: CraftingValidatorProtocol | None = None
    ):
        self.repository = repository
        self.character_service = character_service
        self.building_repository = building_repository
        self.item_service = item_service
        self.character_resource_service = character_resource_service
        self.item_component_service = item_component_service
        self.city_trading_shop_repository = city_trading_shop_repository
        self.character_recipes_repository = character_recipes_repository
        self.character_start_creating_repository = character_start_creating_repository
        self.captcha_adapter = captcha_adapter
        self.template_service = template_service
        self.items_events = items_events
        self.cooldown_seconds = cooldown_seconds
        self.crafting_license_service = crafting_license_service
        self.min_valid_level = min_valid_level
        self.max_valid_tiredness = max_valid_tiredness
        # Валидация вынесена в CraftingValidator; если не передан явно —
        # собирается из тех же зависимостей (обратная совместимость)
        self.validator = validator or CraftingValidator(
            building_repository=building_repository,
            city_trading_shop_repository=city_trading_shop_repository,
            item_component_service=item_component_service,
            character_resource_service=character_resource_service,
            crafting_license_service=crafting_license_service,
            min_valid_level=min_valid_level,
            max_valid_tiredness=max_valid_tiredness,
        )

    async def create_new_item_crafting_action(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        """Создать действие крафта для нового предмета (craft_stage=0)"""
        logger.info(f"Create NEW item crafting action requested for character_id={character_id} recipe_id={recipe_id}")
        
        # Get character info
        character = await self.character_service.get_simple_info_character(character_id)
        logger.debug(
            "Character fetched: id=%s location=%s",
            character.id, character.location_slug
        )

        # ✅ Проверка уровня и усталости (вынесена в CraftingValidator)
        await self.validator.validate_character(character)

        # Get recipe by id and character_id
        recipe = await self.character_recipes_repository.get_for_character(recipe_id, character_id)
        if not recipe:
            logger.warning(
                "Recipe not found for character %s: recipe_id=%s",
                character_id, recipe_id
            )
            raise RecipeNotFoundError(
                character_id=character_id,
                item_slug="unknown",
                quantity=0
            )
        
        logger.debug(
            "Recipe validated: recipe_id=%s item_slug=%s quantity=%s",
            recipe.id, recipe.item_slug, recipe.quantity
        )
        
        item_slug = recipe.item_slug

        # Запрещаем начинать новый крафт предмета, который уже в процессе
        existing = await self.character_start_creating_repository.get_by_character_and_item(
            character_id, item_slug
        )
        if existing:
            logger.warning(
                "Character %s already has started crafting for item %s (stage=%s), rejecting new craft",
                character_id, item_slug, existing.craft_stage
            )
            raise ItemCraftAlreadyStartedError(item_slug=item_slug)
        
        # Get item info
        item = await self.item_service.get_by_slug(item_slug)
        logger.debug("Item fetched: slug=%s location=%s craft_stages=%s", item.slug, item.location_slug, item.craft_stages)
        
        # Проверка локации/лицензии и наличия ресурсов (вынесена в CraftingValidator)
        building = await self.validator.validate_location_and_license(character, item)
        await self.validator.validate_resources(character_id, item_slug)

        # B1: капча сжигается ТОЛЬКО здесь — после того как все проверки пройдены
        await self.captcha_adapter.verify_captcha(captcha)
        logger.info("Captcha verified (and burned) for character_id=%s, proceeding to create", character_id)
        
        # Create crafting action for NEW item (craft_stage=0)
        start_time = datetime.now(UTC)
        finish_time = start_time + timedelta(seconds=self.cooldown_seconds)
        logger.debug(
            "Crafting action timing: start=%s finish=%s",
            start_time, finish_time
        )
        
        status = ItemCreatingStatus.IN_PROGRESS
        craft_stage = 0  # Новый предмет всегда начинается с 0
        message = self.template_service.get_crafting_progress_message(
            location_slug=item.location_slug,
            item_name=item.name,
            stage=1,
            total_stages=item.craft_stages or 1,
            time=self.cooldown_seconds,
        )
        
        creating_action = ItemsCreatingActionCreateSchema(
            character_id=character.id,
            location_slug=building.location_slug,
            status=status,
            message=message,
            start_time=start_time,
            finish_time=finish_time,
            quantity=None,
            craft_stage=craft_stage
        )

        created_action = await self.repository.create(creating_action)
        logger.info("Crafting action created: action_id=%s craft_stage=%s", created_action.id, craft_stage)
        
        # Schedule Celery task
        from ...tasks import finish_creating_task
        character_data = {
            "id": str(character.id),
            "location_slug": character.location_slug
        }
        logger.info("Scheduling finish_creating_task for action_id=%s, item_slug=%s", created_action.id, item_slug)
        result = finish_creating_task.apply_async(
            args=[created_action.id, character_data, item_slug],
            countdown=self.cooldown_seconds,
            task_id=f"finish_creating:{created_action.id}"
        )
        logger.info("Task scheduled, task_id=%s countdown=%s", result.id, self.cooldown_seconds)

        updated_action = await self.repository.update_celery_task_id(
            action_id=created_action.id,
            celery_task_id=result.id
        )
        logger.debug(
            "Updated crafting action with celery_task_id: %s",
            result.id
        )

        await self.character_recipes_repository.decrement_quantity_for_character(recipe.id, character_id)
        logger.info(
            "Decremented recipe quantity in CharacterRecipes: recipe_id=%s character_id=%s",
            recipe.id, character_id
        )

        # Создаём запись CharacterStartCreatingItem с craft_stage=0 сразу,
        # чтобы предмет появился в таблице startedCrafting до завершения первого этапа
        start_creating_data = CharacterStartCreatingItemCreateSchema(
            character_id=character.id,
            item_slug=item_slug,
            craft_stage=0
        )
        await self.character_start_creating_repository.create(start_creating_data)
        
        # 👇 Явный коммит, чтобы Celery-воркер увидел запись
        await self.character_start_creating_repository.session.commit()
        
        logger.info(
            "Created CharacterStartCreatingItem for character_id=%s item_slug=%s with craft_stage=0",
            character.id, item_slug
        )

        logger.info("NEW item crafting action fully initialized: action_id=%s", created_action.id)
        return updated_action
    
    async def continue_item_crafting_action(
        self,
        character_id: uuid.UUID,
        start_creating_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        """Продолжить крафт существующего предмета (craft_stage > 0)"""
        logger.info(
            f"Continue item crafting action requested for character_id={character_id} start_creating_id={start_creating_id}"
        )
        
        # Get character info
        character = await self.character_service.get_simple_info_character(character_id)
        logger.debug(
            "Character fetched: id=%s location=%s",
            character.id, character.location_slug
        )

        # ✅ Проверка уровня и усталости (вынесена в CraftingValidator)
        await self.validator.validate_character(character)

        # Get CharacterStartCreatingItem
        start_creating = await self.character_start_creating_repository.get(start_creating_id)
        if start_creating.character_id != character_id:
            logger.warning(
                "CharacterStartCreatingItem %s does not belong to character %s",
                start_creating_id, character_id
            )
            raise PermissionDeniedError()
        
        logger.debug(
            "CharacterStartCreatingItem fetched: item_slug=%s craft_stage=%s",
            start_creating.item_slug, start_creating.craft_stage
        )
        
        # Get item info
        item = await self.item_service.get_by_slug(start_creating.item_slug)
        logger.debug(
            "Item fetched: slug=%s location=%s craft_stages=%s",
            item.slug, item.location_slug, item.craft_stages
        )
        
        # Проверка локации/лицензии и наличия ресурсов (вынесена в CraftingValidator)
        building = await self.validator.validate_location_and_license(character, item)
        await self.validator.validate_resources(character_id, start_creating.item_slug)

        # B1: капча сжигается ТОЛЬКО здесь — после того как все проверки пройдены
        await self.captcha_adapter.verify_captcha(captcha)
        logger.info("Captcha verified (and burned) for character_id=%s, proceeding to continue", character_id)
        
        # Create crafting action for CONTINUING item
        start_time = datetime.now(UTC)
        finish_time = start_time + timedelta(seconds=self.cooldown_seconds)
        logger.debug(
            "Crafting action timing: start=%s finish=%s",
            start_time, finish_time
        )
        
        status = ItemCreatingStatus.IN_PROGRESS
        current_stage = start_creating.craft_stage
        message = self.template_service.get_crafting_progress_message(
            location_slug=item.location_slug,
            item_name=item.name,
            stage=current_stage + 1,
            total_stages=item.craft_stages or 1,
            time=self.cooldown_seconds,
        )
        
        creating_action = ItemsCreatingActionCreateSchema(
            character_id=character.id,
            location_slug=building.location_slug,
            status=status,
            message=message,
            start_time=start_time,
            finish_time=finish_time,
            quantity=None,
            craft_stage=current_stage
        )

        created_action = await self.repository.create(creating_action)
        logger.info(
            "Crafting action created: action_id=%s craft_stage=%s",
            created_action.id, current_stage
        )
        
        # Schedule Celery task
        from ...tasks import finish_continue_creating_task
        character_data = {
            "id": str(character.id),
            "location_slug": character.location_slug
        }
        logger.info("Scheduling finish_continue_creating_task for action_id=%s, start_creating_id=%s", 
                    created_action.id, start_creating_id)
        result = finish_continue_creating_task.apply_async(
            args=[created_action.id, character_data, start_creating_id],
            countdown=self.cooldown_seconds,
            task_id=f"finish_continue_creating:{created_action.id}"
        )
        logger.info("Task scheduled, task_id=%s countdown=%s", result.id, self.cooldown_seconds)

        updated_action = await self.repository.update_celery_task_id(
            action_id=created_action.id,
            celery_task_id=result.id
        )
        logger.debug(
            "Updated crafting action with celery_task_id: %s",
            result.id
        )

        logger.info("CONTINUE item crafting action fully initialized: action_id=%s", created_action.id)
        return updated_action


class ProcessItemsCreatingActionServiceProtocol(Protocol):
    async def process_new_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        item_slug: str,
    ) -> dict:
        """Обработка завершения крафта нового предмета (craft_stage=0)"""
        ...
    
    async def process_continue_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        start_creating_id: uuid.UUID
    ) -> dict:
        """Обработка завершения крафта существующего предмета (craft_stage > 0)"""
        ...


class ProcessItemsCreatingActionService(ProcessItemsCreatingActionServiceProtocol):
    def __init__(
        self,
        repository: ItemsCreatingActionRepositoryProtocol,
        character_start_creating_repository: CharacterStartCreatingItemRepositoryProtocol,
        item_service: ItemServiceProtocol,
        item_component_service: ItemComponentServiceProtocol,
        character_resource_service: CharacterResourceServiceProtocol,
        character_item_repository: CharacterItemRepositoryProtocol,
        character_service: CharacterServiceClientProtocol,
        character_city_trade_stats_repository: 'CharacterCityTradeStatsRepositoryProtocol',
        item_experience_for_level_service: 'ItemExperienceForLevelServiceProtocol',
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
        redis_publisher: RedisPublisherProtocol | None = None,
        change_tiredness: float = 0.03,
        chance_lose_resource: float = 0.2,
        processor: CraftingResultProcessorProtocol | None = None
    ):
        self.repository = repository
        self.character_start_creating_repository = character_start_creating_repository
        self.item_service = item_service
        self.item_component_service = item_component_service
        self.character_resource_service = character_resource_service
        self.character_item_repository = character_item_repository
        self.character_service = character_service
        self.character_city_trade_stats_repository = character_city_trade_stats_repository
        self.item_experience_for_level_service = item_experience_for_level_service
        self.template_service = template_service
        self.items_events = items_events
        self.redis_publisher = redis_publisher
        self.change_tiredness = change_tiredness
        self.chance_lose_resource = chance_lose_resource
        # Обработка исхода стадии вынесена в CraftingResultProcessor;
        # если не передан явно — собирается из тех же зависимостей
        self.processor = processor or CraftingResultProcessor(
            repository=repository,
            character_start_creating_repository=character_start_creating_repository,
            character_item_repository=character_item_repository,
            character_resource_service=character_resource_service,
            character_service=character_service,
            character_city_trade_stats_repository=character_city_trade_stats_repository,
            item_experience_for_level_service=item_experience_for_level_service,
            template_service=template_service,
            items_events=items_events,
            redis_publisher=redis_publisher,
            change_tiredness=change_tiredness,
            chance_lose_resource=chance_lose_resource,
        )

    async def process_new_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        item_slug: str,
    ) -> dict:
        logger.info(
            "Processing NEW item crafting action: action_id=%s character_id=%s item_slug=%s",
            action_id, character_data["id"], item_slug
        )
        character_id = uuid.UUID(character_data["id"])

        creating_action = await self.repository.get_for_character(action_id, character_id)
        if not creating_action:
            return {"status": "missing"}

        if creating_action.status != ItemCreatingStatus.IN_PROGRESS:
            return {"status": "already_processed"}

        now = datetime.now(UTC)
        if creating_action.finish_time > now:
            remaining = (creating_action.finish_time - now).total_seconds()
            if remaining > 1:
                from ...tasks import finish_creating_task
                finish_creating_task.apply_async(
                    args=[creating_action.id, character_data, item_slug], countdown=int(remaining)
                )
                return {"status": "rescheduled"}

        item = await self.item_service.get_by_slug(item_slug)
        components = await self.item_component_service.get_components_with_resource_names(item_slug)

        character_stats = await self.character_city_trade_stats_repository.get_or_create(
            character_id=character_id,
            location_slug=creating_action.location_slug
        )
        current_level = character_stats.level
        level_record = await self.item_experience_for_level_service.get_current_level(current_level)
        success_rate = level_record.success_rate_one

        success_roll = random.random()

        # Исход стадии (успех/неудача, опыт, усталость, события) применяет CraftingResultProcessor.
        # Для нового предмета стадия всегда считается промежуточной (0 -> 1),
        # предмет выдаётся только в process_continue_creating_action.
        return await self.processor.process(
            creating_action=creating_action,
            item=item,
            components=components,
            item_slug=item_slug,
            character_id=character_id,
            success_rate=success_rate,
            success_roll=success_roll,
            is_final_stage=False,
            new_stage=1,
        )

    async def process_continue_creating_action(
        self,
        action_id: uuid.UUID,
        character_data: dict,
        start_creating_id: uuid.UUID
    ) -> dict:
        logger.info(
            "Processing CONTINUE item crafting action: action_id=%s start_creating_id=%s",
            action_id, start_creating_id
        )
        character_id = uuid.UUID(character_data["id"])

        creating_action = await self.repository.get_for_character(action_id, character_id)
        if not creating_action or creating_action.status != ItemCreatingStatus.IN_PROGRESS:
            return {"status": "missing" if not creating_action else "already_processed"}

        now = datetime.now(UTC)
        if creating_action.finish_time > now:
            remaining = (creating_action.finish_time - now).total_seconds()
            if remaining > 1:
                from ...tasks import finish_continue_creating_task
                finish_continue_creating_task.apply_async(
                    args=[creating_action.id, character_data, start_creating_id], countdown=int(remaining)
                )
                return {"status": "rescheduled"}

        start_creating = await self.character_start_creating_repository.get(start_creating_id)
        item = await self.item_service.get_by_slug(start_creating.item_slug)
        components = await self.item_component_service.get_components_with_resource_names(start_creating.item_slug)

        current_stage = creating_action.craft_stage
        is_final_stage = (current_stage + 1) >= (item.craft_stages or 1)

        character_stats = await self.character_city_trade_stats_repository.get_or_create(
            character_id=character_id, location_slug=creating_action.location_slug
        )
        level_record = await self.item_experience_for_level_service.get_current_level(character_stats.level)
        success_rate = level_record.success_rate_one

        success_roll = random.random()

        # Исход стадии применяет CraftingResultProcessor (списание ресурсов,
        # выдача предмета, опыт, усталость, события) — формулы сохранены 1:1
        return await self.processor.process(
            creating_action=creating_action,
            item=item,
            components=components,
            item_slug=start_creating.item_slug,
            character_id=character_id,
            success_rate=success_rate,
            success_roll=success_roll,
            is_final_stage=is_final_stage,
            new_stage=current_stage + 1,
            start_creating_id=start_creating_id,
        )

class ValidateCreateItemActionServiceProtocol(Protocol):
    async def validate_captcha_and_create_new_item(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        ...
    
    async def validate_captcha_and_continue_item(
        self,
        character_id: uuid.UUID,
        start_creating_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        ...


class ValidateCreateItemActionService(ValidateCreateItemActionServiceProtocol):
    def __init__(
        self,
        creating_checker: ItemsCreatingActionServiceProtocol,
        creating_creator: CreateItemsCreatingActionServiceProtocol
    ):
        self.creating_checker = creating_checker
        self.creating_creator = creating_creator

    async def validate_captcha_and_create_new_item(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        logger.info("Validating for NEW item crafting: character_id=%s recipe_id=%s", character_id, recipe_id)
        
        # Проверка активного крафта (самый дешёвый чек, самый частый конфликт)
        logger.debug("Checking existing crafting process for character_id=%s", character_id)
        exist_another_process = await self.creating_checker.exists_processing_creating_action(character_id)
        if exist_another_process:
            logger.warning("Character %s already has an active crafting process", character_id)
            raise ItemAlreadyCreatingError(character_id)
        
        logger.info("No active crafting process found for character_id=%s. Delegating to creator.", character_id)
        
        # Creator выполнит все проверки (уровень, усталость, лицензия, ресурсы)
        # и только после успешных проверок — verify_captcha перед insert
        action = await self.creating_creator.create_new_item_crafting_action(
            character_id=character_id,
            recipe_id=recipe_id,
            captcha=captcha
        )
        
        logger.info("NEW item crafting action created successfully for character_id=%s action_id=%s", character_id, action.id)
        return action
    
    async def validate_captcha_and_continue_item(
        self,
        character_id: uuid.UUID,
        start_creating_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        logger.info("Validating for CONTINUE item crafting: character_id=%s", character_id)
        
        # Проверка активного крафта
        exist_another_process = await self.creating_checker.exists_processing_creating_action(character_id)
        if exist_another_process:
            raise ItemAlreadyCreatingError(character_id)
        
        logger.info("No active crafting process found for character_id=%s. Delegating to creator.", character_id)
        
        # Creator выполнит все проверки и verify_captcha перед insert
        action = await self.creating_creator.continue_item_crafting_action(
            character_id=character_id,
            start_creating_id=start_creating_id,
            captcha=captcha
        )
        
        return action
