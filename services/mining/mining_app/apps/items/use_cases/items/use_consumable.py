import logging
import random
import uuid

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import ValidationError
from ...adapters.characters import CharacterServiceClientProtocol
from ...events.items import ItemEventsProtocol
from ...requirements import check_item_requirements
from ...services.adapters.item_templates import ItemTemplateServiceProtocol
from ...services.character.character_items import CharacterItemServiceProtocol
from ...weight import recalculate_character_weight

logger = logging.getLogger(__name__)

BOOST_MIN_SECONDS = 2 * 60 * 60   # 2 часа
BOOST_MAX_SECONDS = 4 * 60 * 60   # 4 часа


class UseConsumableUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> StatusOkSchema: ...


class UseConsumableUseCase(UseConsumableUseCaseProtocol):
    def __init__(
        self,
        inventory_service: CharacterItemServiceProtocol,
        characters_client: CharacterServiceClientProtocol,
        items_events: ItemEventsProtocol,
        template_service: ItemTemplateServiceProtocol,
    ):
        self.inventory_service = inventory_service
        self.characters_client = characters_client
        self.items_events = items_events
        self.template_service = template_service

    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> StatusOkSchema:
        inventory_item = await self.inventory_service.get_by_id_and_character(
            inventory_item_id, user.character_id
        )

        if inventory_item is None:
            raise ValidationError(
                field="inventory_item_id",
                message="Предмет не найден в вашем инвентаре.",
            )

        # ═══ ЭСКРОУ: предмет в сделке «заморожен» — использовать нельзя ═══
        if getattr(inventory_item, "deal_id", None) is not None:
            raise ValidationError(
                field="deal_id",
                message="Предмет находится в сделке — сначала уберите его из сделки.",
            )

        item = inventory_item.item

        item_type_value = item.item_type.value if hasattr(item.item_type, 'value') else item.item_type
        if item_type_value.lower() not in ("elixir", "fish"):
            raise ValidationError(field="item_type", message=f"Item type '{item_type_value}' is not consumable")

        # ═══ ПРОВЕРКА ТРЕБОВАНИЙ (уровень, раса, статы) ═══
        character = await self.characters_client.get_character_for_requirements(user.character_id)
        check_item_requirements(item, character)

        # 1. Рыба — это еда: общий кулдаун с Харчевней, 10 минут
        if item_type_value.lower() == "fish":
            effects = self._extract_food_effects(item.ability_parameters)
            if not effects:
                raise ValidationError(field="ability_parameters", message="Item has no effect parameters")

            await self.characters_client.consume_food(
                character_id=user.character_id,
                effects=effects,
                cooldown_seconds=600,
            )
        else:
            # 2. Эликсиры — старая схема через баффы
            effects = self._extract_effects(item.ability_parameters)

            # Fallback: старый формат parameters (buff_type)
            if not effects:
                params = item.parameters or {}
                if params.get("buff_type"):
                    effects = [(params["buff_type"], params.get("buff_value", 0), params.get("buff_duration", 0))]

            if not effects:
                raise ValidationError(field="ability_parameters", message="Item has no effect parameters")

            for buff_type, buff_value, buff_duration in effects:
                try:
                    await self.characters_client.apply_buff(
                        character_id=user.character_id,
                        buff_type=buff_type,
                        value=buff_value,
                        duration_seconds=buff_duration,
                        source="potion",
                        source_name=item.name
                    )
                except ValidationError as e:
                    raise ValidationError(field="buff_type", message=e.message)

        # Потребляем предмет (amount -= 1 или удаление)
        await self.inventory_service.consume_item(inventory_item_id)

        # Пересчёт веса после потребления предмета
        await recalculate_character_weight(
            self.inventory_service, self.characters_client, user.character_id
        )

        # Пересчёт веса после потребления предмета
        await recalculate_character_weight(
            self.inventory_service, self.characters_client, user.character_id
        )

        # ═══ Системное сообщение в чат ═══
        try:
            location_info = await self.characters_client.get_simple_info_character(user.character_id)
            location_slug = location_info.location_slug or "unknown"

            message_text = self.template_service.get_consumable_use_message(item_name=item.name)
            await self.items_events.publish_message(
                ItemMessageEventSchema(
                    event_type="item_consumable_use",
                    character_id=user.character_id,
                    location_slug=location_slug,
                    content=message_text,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[user.character_id],
                )
            )
        except Exception as e:
            logger.warning(f"Failed to publish consumable_use event: {e}")        

        return StatusOkSchema()

    @staticmethod
    def _extract_effects(ability: dict | None) -> list[tuple[str, float, int]]:
        ability = ability or {}
        effects = []
        boost_duration = random.randint(BOOST_MIN_SECONDS, BOOST_MAX_SECONDS)

        # Мгновенное восстановление
        if "health_number" in ability:
            effects.append(("hp_restore", float(ability["health_number"]), 0))
        if "tiredness_percentage" in ability:
            effects.append(("stamina_restore_percent", abs(float(ability["tiredness_percentage"])), 0))

        # Временные бусты статов (2–4 часа)
        if "power_number" in ability:
            effects.append(("strength_boost", int(ability["power_number"]), boost_duration))
        if "agility_number" in ability:
            effects.append(("agility_boost", int(ability["agility_number"]), boost_duration))
        if "lucky_number" in ability:
            effects.append(("luck_boost", int(ability["lucky_number"]), boost_duration))

        return effects

    @staticmethod
    def _extract_food_effects(ability: dict | None) -> list[dict]:
        ability = ability or {}
        effects = []
        if "health_number" in ability:
            effects.append({"effect_type": "hp_restore", "value": float(ability["health_number"])})
        if "tiredness_percentage" in ability:
            effects.append({"effect_type": "stamina_restore_percent", "value": abs(float(ability["tiredness_percentage"]))})
        return effects