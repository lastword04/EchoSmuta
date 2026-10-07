import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Protocol

from shared.enums import ResultStatus
from shared.schemas.mining import MiningActionEventSchema, MonsterAttackEventSchema

from ..adapters.characters_sync import CharacterServiceSyncClient
from ..enums import MiningStatus
from ..events.mining_sync import MiningEventsSync
from ..events.monster_sync import MonsterEventsSync
from ..events.publisher_sync import RedisPublisherSyncProtocol
from ..repositories.location_character_expierence_sync import CharacterLocationStatsSyncRepository
from ..repositories.location_resources_character_sync import (
    LocationResourcesCharacterSyncRepository,
)
from ..repositories.mining_actions_sync import MiningActionSyncRepository
from ..schemas import (
    CharacterLocationStatsReadSchema,
    MiningActionReadSchema,
    MiningActionUpdateSchema,
)
from .character_resource_sync import CharacterResourceSyncService
from .experience_for_level_sync import ExperienceForLevelSyncService
from .location_resources_sync import LocationResourceSyncService
from .location_settings_sync import LocationSettingsSyncService
from .mining_templates import MiningTemplateService
from .monster_location_sync import MonsterLocationSyncService

logger = logging.getLogger(__name__)


class ProcessMiningActionSyncServiceProtocol(Protocol):
    def process_mining_action(self, action_id: uuid.UUID, character_data: dict) -> dict: ...


class ProcessMiningActionSyncService(ProcessMiningActionSyncServiceProtocol):
    def __init__(
        self,
        repository: MiningActionSyncRepository,
        experience_service: ExperienceForLevelSyncService,
        location_settings_service: LocationSettingsSyncService,
        location_resource_service: LocationResourceSyncService,
        location_resources_character_repository: LocationResourcesCharacterSyncRepository,
        location_character_experience_repository: CharacterLocationStatsSyncRepository,
        character_resource_service: CharacterResourceSyncService,
        mining_events: MiningEventsSync,
        monster_events: MonsterEventsSync,
        character_service: CharacterServiceSyncClient,
        monster_service: MonsterLocationSyncService,
        template_service: MiningTemplateService,
        redis_publisher: RedisPublisherSyncProtocol | None = None,
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

    def process_mining_action(self, action_id: uuid.UUID, character_data: dict) -> dict:
        logger.info(
            "Processing mining action: action_id=%s character_id=%s",
            action_id, character_data["id"]
        )

        character_id = uuid.UUID(character_data["id"])
        location_slug = character_data["location_slug"]
        character_tiredness = character_data["tiredness"] + self.change_tiredness
        character_health = character_data["health"]
        character_max_health = character_data["max_health"]
        mining_action = self.repository.get_for_character(action_id, character_id)

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
                # Reschedule через Celery (используем sync task)
                from ..tasks import finish_mining_task
                finish_mining_task.apply_async(
                    args=[mining_action.id, character_data],
                    countdown=int(remaining)
                )
                return {"status": "rescheduled"}

        logger.debug(
            "Mining action %s eligible for result calculation",
            mining_action.id
        )

        character_stats = self.location_character_experience_repository.get_or_create(
            character_id=character_id,
            location_slug=location_slug
        )
        logger.debug(
            "Character stats: level=%s exp=%s add_chance=%s",
            character_stats.level,
            character_stats.experience,
            character_stats.add_chance
        )

        experience_current_level, experience_next_level = self.experience_service.get_current_and_next_level_experience(
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
            logger.debug("Mining roll: base=random - add_chance = %s", mining_chance)
            if mining_chance < chance:
                count_resource += 1
            else:
                break

        if count_resource == 0:
            logger.info(
                "Mining failed for character_id=%s at location=%s",
                character_id, location_slug
            )
            return self._failure_result(
                mining_action, character_stats, character_id, location_slug,
                character_tiredness, character_health, character_max_health
            )

        logger.debug(
            "Mining success! Rolled %s resource(s) before resource type selection.",
            count_resource
        )

        resources = self.location_resources_character_repository.get_all_by_location(location_slug)
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
            return self._failure_result(
                mining_action, character_stats, character_id, location_slug,
                character_tiredness, character_health, character_max_health
            )

        count_resource = min(count_resource, result_resource.current_amount)
        logger.info(
            "Character %s mined %s x %s",
            character_id, count_resource, result_resource.resource_slug
        )

        success_result_status = ResultStatus.SUCCESS
        status = MiningStatus.DONE
        resource_name_cap = result_resource.resource_name.capitalize()
        message = self.template_service.get_message(
            location_slug, status, success_result_status,
            resource=resource_name_cap, amount=count_resource
        )
        action_update = MiningActionUpdateSchema(
            **mining_action.model_dump(exclude={"status", "result_status", "recived_resourse_slug", "count_recived_resource", "message"}),
            status=status,
            message=message,
            result_status=success_result_status,
            recived_resourse_slug=result_resource.resource_slug,
            count_recived_resource=count_resource
        )
        self.repository.update(action_update)
        self.character_resource_service.increment_amount(character_id, result_resource.resource_slug, count_resource)
        new_current_amount = result_resource.current_amount - count_resource

        self.location_resource_service.change_current_amount(location_slug, result_resource.resource_slug, new_current_amount)
        new_experience = character_stats.experience + result_resource.experience_on_resource
        new_level = character_stats.level
        if experience_next_level:
            new_level = new_level + 1 if new_experience >= experience_next_level.experience else new_level
        new_add_chance = 0.0

        self.location_character_experience_repository.update_experience_and_level_and_add_chance(
            character_id, location_slug,
            new_level, new_experience, new_add_chance
        )
        self.character_service.update_tiredness(character_id, character_tiredness)
        logger.info(
            "Mining COMPLETED: character_id=%s action_id=%s resource=%s count=%s",
            character_id, mining_action.id,
            result_resource.resource_slug, count_resource
        )

        monster_attack_event = self._attack_monsters(
            action_id, location_slug, character_id,
            character_health, character_max_health, character_tiredness
        )

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

        self.mining_events.publish_mining_result(event)

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
            
            self.redis_publisher.publish("economy_state_updated", payload)
        except Exception as e:
            logger.error(f"Failed to publish economy state update: {e}")

        return {"status": "ok"}

    def _failure_result(
        self,
        mining_action: MiningActionReadSchema,
        character_stats: CharacterLocationStatsReadSchema,
        character_id: uuid.UUID,
        location_slug: str,
        character_tiredness: float,
        character_health: int,
        character_max_health: int
    ) -> dict:
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
        self.repository.update(action_update)
        location_settings = self.location_settings_service.get_by_slug(location_slug)
        new_add_chance = character_stats.add_chance + location_settings.up_chance_for_unluck
        self.location_character_experience_repository.update_add_chance(
            character_id, location_slug, add_chance=new_add_chance
        )
        self.character_service.update_tiredness(character_id, character_tiredness)

        logger.debug("Failure result processed: new_add_chance=%s", new_add_chance)

        monster_attack_event = self._attack_monsters(
            mining_action.id, location_slug, character_id,
            character_health, character_max_health, character_tiredness
        )

        event = MiningActionEventSchema(
            id=mining_action.id,
            character_id=character_id,
            location_slug=location_slug,
            result_status=result_status,
            monster_attack=monster_attack_event
        )

        self.mining_events.publish_mining_result(event)

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
            
            self.redis_publisher.publish("economy_state_updated", payload)
        except Exception as e:
            logger.error(f"Failed to publish economy state update: {e}")

        return {"status": "ok"}

    def _attack_monsters(
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

            monster = self.monster_service.get_by_slug(location_slug)
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
                self.character_resource_service.increment_amount(character_id, resource_slug, 1)
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