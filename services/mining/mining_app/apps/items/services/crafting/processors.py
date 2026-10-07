"""Обработчик результата стадии крафта (async-версия).

Логика выделена из ``ProcessItemsCreatingActionService``: обработка успешной
финальной стадии, успешной промежуточной стадии, неудачи и публикация событий.
Формулы опыта, шансы, порядок списания ресурсов и коммитов сохранены 1:1.
"""
import logging
import random
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from shared.enums import ResultStatus
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from ....resources.events.publisher import RedisPublisherProtocol
from ....resources.services.character_resource import CharacterResourceServiceProtocol
from ...enums import ItemCreatingStatus
from ...events.items import ItemEventsProtocol
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.crafting.character_start_creating_item import (
    CharacterStartCreatingItemRepositoryProtocol,
)
from ...repositories.crafting.items_creating_action import (
    ItemsCreatingActionRepositoryProtocol,
)
from ...repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepositoryProtocol,
)
from ...schemas import (
    CharacterStartCreatingItemCreateSchema,
    InventoryItemCreateSchema,
    ItemsCreatingActionReadSchema,
    ItemsCreatingActionUpdateSchema,
)
from ...services.adapters.item_templates import ItemTemplateServiceProtocol
from ...services.items.experience_for_level import ItemExperienceForLevelServiceProtocol

logger = logging.getLogger(__name__)


class CraftingResultProcessorProtocol(Protocol):
    """Контракт обработчика результата стадии крафта."""

    async def process(
        self,
        creating_action: ItemsCreatingActionReadSchema,
        item: Any,
        components: Sequence[Any],
        item_slug: str,
        character_id: uuid.UUID,
        success_rate: float,
        success_roll: float,
        is_final_stage: bool,
        new_stage: int,
        start_creating_id: uuid.UUID | None = None,
    ) -> dict:
        ...


class CraftingResultProcessor(CraftingResultProcessorProtocol):
    """Применяет исход стадии крафта и рассылает уведомления."""

    def __init__(
        self,
        repository: ItemsCreatingActionRepositoryProtocol,
        character_start_creating_repository: CharacterStartCreatingItemRepositoryProtocol,
        character_item_repository: CharacterItemRepositoryProtocol,
        character_resource_service: CharacterResourceServiceProtocol,
        character_service,
        character_city_trade_stats_repository: CharacterCityTradeStatsRepositoryProtocol,
        item_experience_for_level_service: ItemExperienceForLevelServiceProtocol,
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
        redis_publisher: RedisPublisherProtocol | None = None,
        change_tiredness: float = 0.03,
        chance_lose_resource: float = 0.2,
    ):
        self.repository = repository
        self.character_start_creating_repository = character_start_creating_repository
        self.character_item_repository = character_item_repository
        self.character_resource_service = character_resource_service
        self.character_service = character_service
        self.character_city_trade_stats_repository = character_city_trade_stats_repository
        self.item_experience_for_level_service = item_experience_for_level_service
        self.template_service = template_service
        self.items_events = items_events
        self.redis_publisher = redis_publisher
        self.change_tiredness = change_tiredness
        self.chance_lose_resource = chance_lose_resource

    async def process(
        self,
        creating_action: ItemsCreatingActionReadSchema,
        item: Any,
        components: Sequence[Any],
        item_slug: str,
        character_id: uuid.UUID,
        success_rate: float,
        success_roll: float,
        is_final_stage: bool,
        new_stage: int,
        start_creating_id: uuid.UUID | None = None,
    ) -> dict:
        """Применяет исход стадии крафта и рассылает уведомления.

        ``start_creating_id=None`` означает ветку нового предмета (craft_stage 0 → 1):
        запись CharacterStartCreatingItem ищется по (character_id, item_slug).
        """
        if success_roll <= success_rate:
            if is_final_stage:
                message = await self._handle_success_final(
                    creating_action=creating_action,
                    item=item,
                    components=components,
                    item_slug=item_slug,
                    character_id=character_id,
                    start_creating_id=start_creating_id,
                )
            else:
                message = await self._handle_success_intermediate(
                    creating_action=creating_action,
                    item=item,
                    item_slug=item_slug,
                    character_id=character_id,
                    new_stage=new_stage,
                    start_creating_id=start_creating_id,
                )
            result_status = ResultStatus.SUCCESS
        else:
            message = await self._handle_failure(
                creating_action=creating_action,
                item=item,
                components=components,
                character_id=character_id,
                is_final_stage=is_final_stage,
            )
            result_status = ResultStatus.FAILURE

        character = await self.character_service.get_simple_info_character(character_id)
        await self.character_service.update_tiredness(character_id, character.tiredness + self.change_tiredness)

        await self._publish_events(
            character_id=character_id,
            location_slug=item.location_slug,
            message=message,
            result_status=result_status,
            item_slug=item_slug,
        )

        return {"status": "ok"}

    async def _handle_success_final(
        self,
        creating_action: ItemsCreatingActionReadSchema,
        item: Any,
        components: Sequence[Any],
        item_slug: str,
        character_id: uuid.UUID,
        start_creating_id: uuid.UUID | None,
    ) -> str:
        """Финальная стадия: списание ВСЕХ ресурсов, выдача предмета, удаление start_creating, опыт."""
        # Финальная стадия: выдаем предмет И списываем ВСЕ ресурсы
        for component in components:
            await self.character_resource_service.decrement_amount(
                character_id, component.resource_slug, component.quantity
            )
        logger.info(
            "Deducted all resources for character_id=%s item_slug=%s (final stage)",
            character_id, item_slug
        )

        item_data = InventoryItemCreateSchema(
            item_slug=item_slug, amount=self._calculate_output_amount(item),
            expired_date=self._calculate_expired_date(item),
            used_count=(item.parameters or {}).get("max_used"),
            wear=0 if (item.parameters or {}).get("max_wear") else None,
        )
        await self.character_item_repository.add_item(character_id, item_data)

        await self.character_start_creating_repository.delete(start_creating_id)

        message = self.template_service.get_crafting_success_message(
            location_slug=item.location_slug, item_name=item.name, amount=item_data.amount
        )

        action_update = ItemsCreatingActionUpdateSchema(
            **creating_action.model_dump(exclude={"status", "result_status", "recived_item_slug", "message", "quantity"}),
            status=ItemCreatingStatus.DONE, result_status=ResultStatus.SUCCESS,
            recived_item_slug=item_slug, quantity=item_data.amount,
            message=message
        )
        await self.repository.update(action_update)

        # ✅ Опыт ТОЛЬКО за финальную стадию
        craft_exp = getattr(item, 'craft_experience', None) or 0
        if craft_exp > 0:
            await self._add_experience_and_check_level_up(character_id, item.location_slug, craft_exp)

        await self.repository.session.commit()

        # Пересчёт веса персонажа после выдачи предмета (эталон: purchase_items.py:192-196)
        weight = await self.character_item_repository.get_total_weight(character_id)
        await self.character_service.update_weight(character_id, float(weight))

        return message

    async def _handle_success_intermediate(
        self,
        creating_action: ItemsCreatingActionReadSchema,
        item: Any,
        item_slug: str,
        character_id: uuid.UUID,
        new_stage: int,
        start_creating_id: uuid.UUID | None,
    ) -> str:
        """Промежуточная стадия: повышаем craft_stage (ресурсы НЕ списываем)."""
        if start_creating_id is None:
            # Ветка нового предмета: обновляем существующую запись с craft_stage=0
            existing_start_creating = await self.character_start_creating_repository.get_by_character_and_item(
                character_id, item_slug
            )
            if existing_start_creating:
                await self.character_start_creating_repository.update_craft_stage(
                    start_creating_id=existing_start_creating.id,
                    craft_stage=new_stage
                )
                logger.info(
                    "Updated CharacterStartCreatingItem craft_stage 0 → 1 for character_id=%s item_slug=%s",
                    character_id, item_slug
                )
            else:
                # Fallback: если запись не нашлась (не должно происходить), создаём
                start_creating_data = CharacterStartCreatingItemCreateSchema(
                    character_id=character_id, item_slug=item_slug, craft_stage=new_stage
                )
                await self.character_start_creating_repository.create(start_creating_data)
                logger.warning(
                    "CharacterStartCreatingItem not found, created new for character_id=%s item_slug=%s",
                    character_id, item_slug
                )

            # Ресурсы здесь НЕ списываем: предмет выдаётся только в
            # _handle_success_final (ветка is_final_stage), там и списание.
        else:
            # Ветка продолжения крафта
            await self.character_start_creating_repository.update_craft_stage(
                start_creating_id=start_creating_id, craft_stage=new_stage
            )

        message = self.template_service.get_crafting_stage_success_message(
            location_slug=item.location_slug, item_name=item.name, stage=new_stage
        )

        action_update = ItemsCreatingActionUpdateSchema(
            **creating_action.model_dump(exclude={"status", "result_status", "recived_item_slug", "message", "quantity"}),
            status=ItemCreatingStatus.DONE, result_status=ResultStatus.SUCCESS,
            recived_item_slug=item_slug, quantity=None,
            message=message
        )
        await self.repository.update(action_update)

        # ✅ Опыт ТОЛЬКО для одностадийных предметов (ветка нового предмета)
        if start_creating_id is None and (item.craft_stages is None or item.craft_stages == 1):
            craft_exp = getattr(item, 'craft_experience', None) or 0
            if craft_exp > 0:
                await self._add_experience_and_check_level_up(character_id, item.location_slug, craft_exp)

        await self.repository.session.commit()

        return message

    async def _handle_failure(
        self,
        creating_action: ItemsCreatingActionReadSchema,
        item: Any,
        components: Sequence[Any],
        character_id: uuid.UUID,
        is_final_stage: bool,
    ) -> str:
        """Неудача: шанс потери одного ресурса (кроме финальной стадии), обновление статуса."""
        lost_resource_slug = None
        if is_final_stage:
            message = self.template_service.get_crafting_stage_failure_message(
                location_slug=item.location_slug, item_name=item.name
            )
        else:
            lose_resource_roll = random.random()
            if lose_resource_roll <= self.chance_lose_resource and components:
                random_component = random.choice(components)
                lost_resource_slug = random_component.resource_slug
                await self.character_resource_service.decrement_amount(character_id, lost_resource_slug, 1)
                message = self.template_service.get_crafting_stage_failure_with_loss_message(
                    location_slug=item.location_slug, item_name=item.name, resource_name=random_component.resource_name
                )
            else:
                message = self.template_service.get_crafting_stage_failure_message(
                    location_slug=item.location_slug, item_name=item.name
                )

        action_update = ItemsCreatingActionUpdateSchema(
            **creating_action.model_dump(exclude={"status", "result_status", "lost_resource", "message", "quantity"}),
            status=ItemCreatingStatus.DONE, result_status=ResultStatus.FAILURE,
            lost_resource=lost_resource_slug, quantity=None, message=message
        )
        await self.repository.update(action_update)
        await self.repository.session.commit()

        return message

    async def _publish_events(
        self,
        character_id: uuid.UUID,
        location_slug: str,
        message: str,
        result_status: ResultStatus,
        item_slug: str,
    ) -> None:
        """Отправка сообщения в ItemEvents и события для фронта (WS)."""
        await self.items_events.publish_message(ItemMessageEventSchema(
            event_type="crafting_stage_result", character_id=character_id, location_slug=location_slug,
            content=message, scope=ItemMessageScope.PRIVATE, target_user_ids=[character_id]
        ))

        if self.redis_publisher:
            try:
                payload = {
                    "event_type": "economy_state_updated",
                    "data": {
                        "action": "crafting_stage_completed",
                        "initiator_character_id": str(character_id),
                        "location_slug": location_slug,
                        "message": message,
                        "result_status": "success" if result_status == ResultStatus.SUCCESS else "failure",
                        "item_slug": item_slug,
                    }
                }
                await self.redis_publisher.publish("economy_state_updated", payload)
            except Exception as e:
                logger.error(f"Failed to publish crafting economy state update: {e}")

    async def _add_experience_and_check_level_up(
        self,
        character_id: uuid.UUID,
        location_slug: str,
        gained_experience: int
    ) -> tuple[int, int, bool]:
        """Начисление опыта крафта и проверка повышения уровня."""
        # 1. Получаем или создаем статистику
        character_stats = await self.character_city_trade_stats_repository.get_or_create(
            character_id=character_id,
            location_slug=location_slug
        )

        _, experience_next_level = await self.item_experience_for_level_service.get_current_and_next_level_experience(
            current_level=character_stats.level
        )

        # 2. Считаем новый опыт
        new_experience = character_stats.experience + gained_experience
        new_level = character_stats.level
        did_level_up = False

        if experience_next_level and new_experience >= experience_next_level.experience:
            new_level += 1
            did_level_up = True

        # 3. Обновляем в БД
        await self.character_city_trade_stats_repository.update_experience_and_level(
            character_id=character_id,
            location_slug=location_slug,
            level=new_level,
            experience=new_experience
        )

        # 4. ✅ ГАРАНТИРОВАННЫЙ КОММИТ
        await self.character_city_trade_stats_repository.session.commit()

        return new_level, new_experience, did_level_up

    def _calculate_output_amount(self, item) -> int:
        if item.min_output_quantity is None or item.max_output_quantity is None:
            return 1
        return random.randint(item.min_output_quantity, item.max_output_quantity)

    def _calculate_expired_date(self, item) -> datetime | None:
        if item.min_shelf_life_days is None or item.max_shelf_life_days is None:
            return None
        shelf_life_days = random.randint(item.min_shelf_life_days, item.max_shelf_life_days)
        return datetime.now(UTC) + timedelta(days=shelf_life_days)
