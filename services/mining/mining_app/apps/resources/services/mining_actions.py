import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

from celery.result import AsyncResult

from shared.enums import ResultStatus
from shared.schemas.captcha import CaptchaVerificationRequest
from shared.schemas.mining import MiningActionEventSchema, MonsterAttackEventSchema

from ..adapters.captcha import CaptchaServiceClientProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..enums import MiningStatus
from ..events.mining import MiningEventsProtocol
from ..events.monster import MonsterEventsProtocol
from ..events.publisher import RedisPublisherProtocol
from ..exceptions import (
    InsufficientCharacterLevelError,
    InsufficientCharacterTirednessError,
    ResourceAlreadyMiningError,
)
from ..repositories.location_character_expierence import CharacterLocationStatsRepositoryProtocol
from ..repositories.location_resources_character import LocationResourcesCharacterRepositoryProtocol
from ..repositories.mining_actions import MiningActionRepositoryProtocol
from ..schemas import (
    CharacterLocationStatsReadSchema,
    MiningActionCreateSchema,
    MiningActionReadSchema,
    MiningActionResponseSchema,
    MiningActionUpdateSchema,
)
from .character_resource import CharacterResourceServiceProtocol
from .experience_for_level import ExperienceForLevelServiceProtocol
from .location_resources import LocationResourceServiceProtocol
from .location_settings import LocationSettingsServiceProtocol
from .mining_templates import MiningTemplateServiceProtocol
from .monster_location import MonsterLocationServiceProtocol

logger = logging.getLogger(__name__)

class MiningActionServiceProtocol(Protocol):
    async def get_proccessing_mining_action(self, character_id: uuid.UUID) -> MiningActionResponseSchema:
        ...

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> MiningActionReadSchema:
        ...

    async def exists_processing_mining_action(self, character_id: uuid.UUID) -> bool:
        ...

class MiningActionService(MiningActionServiceProtocol):
    def __init__(
        self,
        repository: MiningActionRepositoryProtocol
    ):
        self.repository = repository

    async def get_proccessing_mining_action(self, character_id: uuid.UUID) -> MiningActionResponseSchema:
        action = await self.repository.get_proccessing_mining_action(character_id)
        if action is None:
            return MiningActionResponseSchema(
                status=MiningStatus.DONE,
                location_slug=None
            )
        return MiningActionResponseSchema(
            id=action.id,
            status=action.status,
            location_slug=action.location_slug,
            message=action.message,
            remaining_time_seconds=int((action.finish_time - datetime.now(UTC)).total_seconds()),
            finish_time=action.finish_time
        )

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> MiningActionReadSchema:
        return await self.repository.get_for_character(action_id, character_id)
    
    async def exists_processing_mining_action(self, character_id: uuid.UUID) -> bool:
        return await self.repository.exists_processing_mining_action(character_id)

class CancelMiningProcessServiceProtocol(Protocol):
    async def cancel_mining(self, character_id: uuid.UUID) -> bool:
        ...

class CancelMiningProcessService(CancelMiningProcessServiceProtocol):
    def __init__(self, repository: MiningActionRepositoryProtocol):
        self.repository = repository

    async def cancel_mining(self, character_id: uuid.UUID) -> bool:
        mining = await self.repository.get_proccessing_mining_action(character_id)
        if not mining or not mining.celery_task_id:
            logger.warning("No active mining action found for character %s", character_id)
            return False
            
        logger.info("Attempting to cancel mining task %s for character %s", 
                   mining.celery_task_id, character_id)
        
        try:
            from ....core.celery_app import celery_app
            
            # Создаем отдельное соединение для revocation
            with celery_app.connection():
                task_result = AsyncResult(mining.celery_task_id, app=celery_app)
                
                if task_result.state in ["PENDING", "RECEIVED", "STARTED"]:
                    # revoke использует соединение из app по умолчанию
                    task_result.revoke(terminate=True, signal='SIGTERM')
                    logger.info("Celery task %s successfully revoked for character %s", 
                               mining.celery_task_id, character_id)
                else:
                    logger.info("Task %s already in state %s, cannot revoke", 
                               mining.celery_task_id, task_result.state)
                    return False
                    
        except Exception as e:
            logger.error("Failed to revoke Celery task %s: %s", mining.celery_task_id, str(e))
            return False

        await self.repository.cancel_mining(mining.id)
        logger.info("Mining action %s cancelled for character %s", mining.id, character_id)
        return True


class CreateMiningActionServiceProtocol(Protocol):
    async def create_mining_action(
        self,
        character_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> MiningActionReadSchema:
        ...

class CreateMiningActionService(CreateMiningActionServiceProtocol):
    def __init__(
        self,
        repository: MiningActionRepositoryProtocol,
        character_service: CharacterServiceClientProtocol,
        template_service: MiningTemplateServiceProtocol,
        captcha_adapter: CaptchaServiceClientProtocol,
        cooldown_seconds: int = 180,
        min_valid_level: int = 3,
        max_valid_tiredness: float = 0.495
    ):
        self.repository = repository
        self.character_service = character_service
        self.template_service = template_service
        self.captcha_adapter = captcha_adapter
        self.cooldown_seconds = cooldown_seconds
        self.min_valid_level = min_valid_level
        self.max_valid_tiredness = max_valid_tiredness

    async def create_mining_action(
        self,
        character_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> MiningActionReadSchema:
        logger.info(f"Create mining action requested for character_id={character_id}")
        character = await self.character_service.get_simple_info_character(character_id)
        logger.debug(
            "Character fetched: id=%s level=%s tiredness=%s location=%s",
            character.id, character.level, character.tiredness, character.location_slug
        )
        if character.level < self.min_valid_level:
            logger.warning(
                "Character %s does not meet level requirement: %s < %s",
                character.id, character.level, self.min_valid_level
            )
            raise InsufficientCharacterLevelError(required_level=self.min_valid_level, current_level=character.level)
        if character.tiredness > self.max_valid_tiredness:
            logger.warning(
                "Character %s tiredness too high: %s > %s",
                character.id, character.tiredness, self.max_valid_tiredness
            )
            raise InsufficientCharacterTirednessError(required_tiredness=self.max_valid_tiredness, current_tiredness=character.tiredness)

        # B1-resources: капча сжигается ТОЛЬКО здесь — после всех проверок (level/tiredness),
        # непосредственно перед созданием экшена (insert)
        await self.captcha_adapter.verify_captcha(captcha)
        logger.info("Captcha verified (and burned) for character_id=%s, proceeding to create", character_id)

        start_time = datetime.now(UTC)
        finish_time = start_time + timedelta(seconds=self.cooldown_seconds)
        logger.debug(
            "Mining action timing: start=%s finish=%s",
            start_time, finish_time
        )
        status = MiningStatus.IN_PROGRESS
        message = self.template_service.get_message(character.location_slug,
                                                    status, None, time=self.cooldown_seconds)
        mining_action = MiningActionCreateSchema(
            character_id=character.id,
            location_slug=character.location_slug,
            status=status,
            message=message,
            start_time=start_time,
            finish_time=finish_time
        )

        created_action = await self.repository.create(mining_action)
        logger.info("Mining action created: action_id=%s", created_action.id)
        from ..tasks import finish_mining_task
        character_data = {
            "id": str(character.id),
            "location_slug": character.location_slug,
            "tiredness": character.tiredness,
            "health": character.health,
            "max_health": character.max_health
        }
        result = finish_mining_task.apply_async(
            args=[created_action.id, character_data],
            countdown=self.cooldown_seconds,
            task_id=f"finish_mining:{created_action.id}"
        )
        logger.info(
            "Celery task scheduled: task_id=%s countdown=%s",
            result.id, self.cooldown_seconds
        )

        updated_action = await self.repository.update_celery_task_id(
            action_id=created_action.id,
            celery_task_id=result.id
        )
        logger.debug(
            "Updated mining action with celery_task_id: %s",
            result.id
        )

        logger.info("Mining action fully initialized: action_id=%s", created_action.id)
        return updated_action

    
class ValidateCreateMiningActionServiceProtocol(Protocol):
    async def validate_captcha_and_mine(
        self,
        character_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> MiningActionReadSchema:
        ...

class ValidateCreateMiningActionService(ValidateCreateMiningActionServiceProtocol):
    def __init__(self, mining_checker: MiningActionServiceProtocol,
                 mining_creator: CreateMiningActionServiceProtocol):
        self.mining_checker = mining_checker
        self.mining_creator = mining_creator

    async def validate_captcha_and_mine(
        self,
        character_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> MiningActionReadSchema:
        logger.info("Validating mining for character_id=%s", character_id)
        logger.debug("Checking existing mining process for character_id=%s", character_id)
        exist_another_process = await self.mining_checker.exists_processing_mining_action(character_id)
        if exist_another_process:
            logger.warning(
                "Character %s already has an active mining process",
                character_id
            )
            raise ResourceAlreadyMiningError(character_id)
        
        logger.info("No active mining process found for character_id=%s. Delegating to creator.", character_id)

        # Creator выполнит все проверки (level, tiredness)
        # и только после успешных проверок — verify_captcha перед insert
        action = await self.mining_creator.create_mining_action(
            character_id=character_id,
            captcha=captcha
        )
        logger.info(
            "Mining action created successfully for character_id=%s action_id=%s",
            character_id, action.id
        )

        return action
    
class ProcessMiningActionServiceProtocol(Protocol):
    async def process_mining_action(
        self,
        action_id: uuid.UUID,
        character_data: dict
    ) -> dict:
        ...

class ProcessMiningActionService(ProcessMiningActionServiceProtocol):
    def __init__(
        self,
        repository: MiningActionRepositoryProtocol,
        experience_service: ExperienceForLevelServiceProtocol,
        location_settings_service: LocationSettingsServiceProtocol,
        location_resource_service: LocationResourceServiceProtocol,
        location_resources_character_repository: LocationResourcesCharacterRepositoryProtocol,
        location_character_experience_repository: CharacterLocationStatsRepositoryProtocol,
        character_resource_service: CharacterResourceServiceProtocol,
        mining_events: MiningEventsProtocol,
        monster_events: MonsterEventsProtocol,
        character_service: CharacterServiceClientProtocol,
        monster_service: MonsterLocationServiceProtocol,
        template_service: MiningTemplateServiceProtocol,
        redis_publisher: RedisPublisherProtocol | None = None,
        change_tiredness: float = 0.03,
        min_attack_monster_health_percentage: float = 0.70,
        min_attack_monster_tiredness: float = 0.25,
        default_monster_attack_chance: float = 0.15,
        default_attack_monster_standart: float = 0.75
    ):
        self.repository = repository
        self.experience_service = experience_service
        self.location_settings_service = location_settings_service
        self.location_resource_service = location_resource_service
        self.location_resources_character_repository = location_resources_character_repository
        self.location_character_experience_repository = location_character_experience_repository
        self.character_resource_service = character_resource_service
        self.mining_events = mining_events
        self.monster_events = monster_events
        self.character_service = character_service
        self.monster_service = monster_service
        self.template_service = template_service
        self.redis_publisher = redis_publisher
        self.change_tiredness = change_tiredness
        self.min_attack_monster_health_percentage = min_attack_monster_health_percentage
        self.min_attack_monster_tiredness = min_attack_monster_tiredness
        self.default_monster_attack_chance = default_monster_attack_chance
        self.default_attack_monster_standart = default_attack_monster_standart

    async def process_mining_action(
        self,
        action_id: uuid.UUID,
        character_data: dict
    ) -> dict:
        logger.info(
            "Processing mining action: action_id=%s character_id=%s",
            action_id, character_data["id"]
        )
        
        character_id = uuid.UUID(character_data["id"])
        location_slug = character_data["location_slug"]
        character_tiredness = character_data["tiredness"] + self.change_tiredness
        character_health = character_data["health"]
        character_max_health = character_data["max_health"]
        mining_action = await self.repository.get_for_character(action_id, character_id)

        if not mining_action:
            logger.warning(
                "Mining action %s not found for character_id=%s",
                action_id, character_id
            )
            return {"status": "missing"}

        logger.debug(
            "Mining action fetched: status=%s finish_time=%s",
            mining_action.status, mining_action.finish_time
        )

        if mining_action.status != MiningStatus.IN_PROGRESS:
            logger.info(
                "Mining action %s already processed (status=%s)",
                mining_action.id, mining_action.status
            )
            return {"status": "already_processed"}
        
        now = datetime.now(UTC)
        if mining_action.finish_time > now:
            remaining = (mining_action.finish_time - now).total_seconds()
            if remaining > 1:
                logger.info(
                    "Mining action %s executed too early, rescheduling by %s seconds",
                    mining_action.id, int(remaining)
                )                
                from ..tasks import finish_mining_task
                finish_mining_task.apply_async(args=[mining_action.id, character_data], countdown=int(remaining))
                return {"status": "rescheduled"}

        logger.debug(
            "Mining action %s eligible for result calculation",
            mining_action.id
        )

        character_stats = await self.location_character_experience_repository.get_or_create(
            character_id=character_id,
            location_slug=location_slug
        )
        logger.debug(
            "Character stats: level=%s exp=%s add_chance=%s",
            character_stats.level,
            character_stats.experience,
            character_stats.add_chance
        )

        experience_current_level, experience_next_level = await self.experience_service.get_current_and_next_level_experience(
            current_level=character_stats.level
        )

        chances = [
            experience_current_level.success_rate_one + character_stats.add_chance, 
            experience_current_level.success_rate_two, 
            experience_current_level.success_rate_three
        ]

        count_resource = 0
        for chance in chances:
            mining_chance = random.random() 
            logger.debug(
            "Mining roll: base=random - add_chance = %s",
            mining_chance
        )
            if mining_chance < chance:
                count_resource += 1
            else:
                break        
        
        if count_resource == 0:
            logger.info(
                "Mining failed for character_id=%s at location=%s",
                character_id, location_slug
            )
            return await self._failure_result(
                mining_action, character_stats, character_id, location_slug, character_tiredness, character_health, character_max_health
            )

        logger.debug(
            "Mining success! Rolled %s resource(s) before resource type selection.",
            count_resource
        )
        
        resources = await self.location_resources_character_repository.get_all_by_location(location_slug)
        resource_chance = random.random()

        result_resource = None
        resource_chance_cumulative = 0.0
        for resource in resources:
            resource_chance_cumulative += resource.chance
            if resource_chance <= resource_chance_cumulative:
                result_resource = resource
                break
        
        if not result_resource:
            logger.error("Sum of resources chance < 1. Resource roll failed.") 
            raise ValueError("Error, all resurces not 100%")
        
        logger.debug(
            "Chosen resource: slug=%s amount_left=%s",
            result_resource.resource_slug, result_resource.current_amount
        )
        if result_resource.current_amount <= 0:
            logger.info(
                "Resource depleted: %s at location %s",
                result_resource.resource_slug, location_slug
            )
            return await self._failure_result(mining_action, character_stats, character_id, location_slug, character_tiredness,
                                              character_health, character_max_health)
        
        count_resource = min(count_resource, result_resource.current_amount)
        logger.info(
            "Character %s mined %s x %s",
            character_id, count_resource, result_resource.resource_slug
        )

        success_result_status = ResultStatus.SUCCESS
        status = MiningStatus.DONE
        resource_name_cap = resource.resource_name.capitalize()
        message = self.template_service.get_message(location_slug, status, success_result_status, 
                                                    resource=resource_name_cap, amount=count_resource)
        action_update = MiningActionUpdateSchema(
            **mining_action.model_dump(exclude={"status", "result_status", "recived_resourse_slug", "count_recived_resource", "message"}),
            status=status,
            message=message,
            result_status=success_result_status,
            recived_resourse_slug=result_resource.resource_slug,
            count_recived_resource=count_resource
        )
        await self.repository.update(action_update)
        await self.character_resource_service.increment_amount(character_id, result_resource.resource_slug, count_resource)
        new_current_amount = result_resource.current_amount - count_resource

        await self.location_resource_service.change_current_amount(location_slug, result_resource.resource_slug, new_current_amount)
        new_experience = character_stats.experience + result_resource.experience_on_resource
        new_level = character_stats.level
        if experience_next_level:
            new_level = new_level + 1 if new_experience >= experience_next_level.experience else new_level
        new_add_chance = 0.0
        
        await self.location_character_experience_repository.update_experience_and_level_and_add_chance(
            character_id, location_slug,
            new_level, new_experience, new_add_chance
        )
        await self.character_service.update_tiredness(character_id, character_tiredness)
        logger.info(
            "Mining COMPLETED: character_id=%s action_id=%s resource=%s count=%s",
            character_id, mining_action.id,
            result_resource.resource_slug, count_resource
        )

        monster_attack_event = await self._attack_monsters(action_id, location_slug, character_id, character_health, character_max_health, character_tiredness)
        
        event = MiningActionEventSchema(
                id=mining_action.id,
                character_id=character_id,
                location_slug=location_slug,
                result_status=success_result_status,
                recived_resourse_slug=result_resource.resource_slug,
                recived_resourse_name=result_resource.resource_name,
                count_recived_resource=count_resource,
                monster_attack=monster_attack_event
            )
        
        await self.mining_events.publish_mining_result(event)

        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "mining_finished",
                    "initiator_character_id": str(character_id),
                    "location_slug": location_slug,
                    "message": message,
                    "result_status": success_result_status.value,
                }
            }
            
            await self.redis_publisher.publish("economy_state_updated", payload)
        except Exception as e:
            logger.error(f"Failed to publish economy state update: {e}")

        return {"status": "ok"}
        
    
    async def _failure_result(self, mining_action: MiningActionReadSchema,
                              character_stats: CharacterLocationStatsReadSchema,
                              character_id: uuid.UUID, location_slug: str,
                              character_tiredness: float,
                              character_health: int, character_max_health: int) -> dict:
        logger.info(
            "Processing mining FAILURE for character_id=%s action_id=%s",
            character_id, mining_action.id
        )
        
        status = MiningStatus.DONE
        result_status = ResultStatus.FAILURE
        message = self.template_service.get_message(location_slug, status, result_status)
        action_update = MiningActionUpdateSchema(
            **mining_action.model_dump(exclude={"status", "result_status", "message"}),
            status=status,
            result_status=result_status,
            message=message
        )
        await self.repository.update(action_update)
        location_settings = await self.location_settings_service.get_by_slug(location_slug)
        new_add_chance = character_stats.add_chance + location_settings.up_chance_for_unluck
        await self.location_character_experience_repository.update_add_chance(character_id, 
                                                                                location_slug,
                                                                                add_chance=new_add_chance)
        await self.character_service.update_tiredness(character_id, character_tiredness)

        logger.debug(
            "Failure result processed: new_add_chance=%s",
            new_add_chance
        )

        monster_attack_event = await self._attack_monsters(mining_action.id, location_slug, character_id, character_health, character_max_health, character_tiredness)

        event = MiningActionEventSchema(
            id=mining_action.id,
            character_id=character_id,
            location_slug=location_slug,
            result_status=result_status,
            monster_attack=monster_attack_event
        )

        await self.mining_events.publish_mining_result(event)

        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "mining_finished",
                    "initiator_character_id": str(character_id),
                    "location_slug": location_slug,
                    "message": message,
                    "result_status": result_status.value,
                }
            }
            await self.redis_publisher.publish("economy_state_updated", payload)
        except Exception as e:
            logger.error(f"Failed to publish economy state update: {e}")

        return {"status": "ok"}


    async def _attack_monsters(
        self,
        mining_id: uuid.UUID,
        location_slug: str,
        character_id: uuid.UUID,
        character_health: int,
        character_max_health: int,
        character_tiredness: float
    ) -> MonsterAttackEventSchema | None:

        logger.info(
            "Checking monster attack possibility: mining_id=%s character_id=%s location=%s",
            mining_id, character_id, location_slug
        )

        health_percentage = character_health / character_max_health
        logger.debug(
            "Character state: health=%s/%s (%.4f), tiredness=%.4f",
            character_health, character_max_health, health_percentage, character_tiredness
        )

        monster_attack_event = None

        # Проверяем возможность атаки
        if (
            health_percentage < self.min_attack_monster_health_percentage
            or character_tiredness > self.min_attack_monster_tiredness
        ):
            logger.info(
                "Monster attack skipped due to insufficient conditions: "
                "health_percentage=%.4f (min=%.4f), tiredness=%.4f (max=%.4f)",
                health_percentage,
                self.min_attack_monster_health_percentage,
                character_tiredness,
                self.min_attack_monster_tiredness
            )

        monster_attack_chance = random.random()
        logger.debug(
            "Monster attack roll: %.5f <= %.5f?",
            monster_attack_chance,
            self.default_monster_attack_chance
        )

        if monster_attack_chance <= self.default_monster_attack_chance:
            logger.info(
                "Monster attacks character_id=%s at location=%s",
                character_id, location_slug
            )

            monster = await self.monster_service.get_by_slug(location_slug)
            logger.debug("Monster data fetched: %s", monster)

            standart_monster_chance = random.random()
            is_standart_monster = standart_monster_chance <= self.default_attack_monster_standart

            logger.debug(
                "Monster type roll: %.5f => is_standart=%s",
                standart_monster_chance, is_standart_monster
            )

            monster_name, resource_slug = (
                (monster.standart_monster_name, monster.standart_monster_skin_slug)
                if is_standart_monster
                else (monster.improved_monster_name, monster.improved_monster_skin_slug)
            )

            logger.info(
                "Monster selected: name=%s is_standart=%s resource=%s",
                monster_name, is_standart_monster, resource_slug
            )

            logger.debug("Monster attack PROCESS")

            # TODO: change on battle
            is_win = random.random() <= 0.5
            logger.info(
                "Battle result: character_id=%s %s",
                character_id,
                "WIN" if is_win else "LOSE"
            )

            if is_win:
                await self.character_resource_service.increment_amount(character_id, resource_slug, 1)
                logger.info(
                    "Character %s received resource '%s' x1",
                    character_id, resource_slug
                )

            monster_attack_event = MonsterAttackEventSchema(
                monster_name=monster_name,
                is_standart_monster=is_standart_monster,
                is_win=is_win
            )

        logger.debug(
            "Monster attack ended for mining_id=%s character_id=%s",
            mining_id, character_id
        )
        return monster_attack_event


