import logging
import uuid
from typing import Protocol, Self

from .....core.utils.exceptions import ModelFieldNotFoundException, ValidationError
from ....resources.events.publisher import RedisPublisherProtocol
from ...adapters.characters import CharacterServiceClientProtocol
from ...enums import ItemType
from ...exceptions import (
    CharacterNotInItemLocationError,
    CharacterWeightExceededError,  # ✅ ДОБАВИТЬ ИМПОРТ
    ShopCapacityExceededError,
)
from ...repositories.character.character_equipment import (
    CharacterEquipmentRepositoryProtocol,
)
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ...schemas import LocationItemsGroupedSchema
from ..character.character_items import CharacterItemServiceProtocol

logger = logging.getLogger(__name__)


class ShopItemServiceProtocol(Protocol):
    async def list_item_to_shop(
        self: Self,
        character_id: uuid.UUID,
        item_id: uuid.UUID,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        ...

    async def withdraw_item_from_shop(
        self: Self,
        character_id: uuid.UUID,
        item_id: uuid.UUID,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        ...


class ShopItemService(ShopItemServiceProtocol):
    def __init__(
        self: Self,
        character_item_repository: CharacterItemRepositoryProtocol,
        shop_repository: CityTradingShopCharacterRepositoryProtocol,
        shop_settings_repository: CityTradingShopSettingsRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        character_item_service: CharacterItemServiceProtocol,
        equipment_repository: CharacterEquipmentRepositoryProtocol,
        redis_publisher: RedisPublisherProtocol,
    ):
        self.character_item_repository = character_item_repository
        self.shop_repository = shop_repository
        self.shop_settings_repository = shop_settings_repository
        self.character_client = character_client
        self.character_item_service = character_item_service
        self.equipment_repository = equipment_repository
        self.redis_publisher = redis_publisher

    async def list_item_to_shop(
        self: Self,
        character_id: uuid.UUID,
        item_id: uuid.UUID,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        # 1. Получаем InventoryItem по ID и character_id с подгрузкой Item (проверка владельца)
        inventory_item = await self.character_item_repository.get_by_id_and_character(item_id, character_id)
        # ═══ ЭСКРОУ: предмет в сделке «заморожен» — в лавку нести нельзя ═══
        if getattr(inventory_item, "deal_id", None) is not None:
            raise ValidationError(
                field="deal_id",
                message="Предмет находится в сделке — сначала уберите его из сделки.",
            )
        if await self.equipment_repository.get_by_inventory_item(item_id):
            raise ValidationError(field="inventory_item_id", message="Equipped item cannot be moved to a shop")

        # ═══ ДОМА: предмет, установленный в доме, в лавку нести нельзя ═══
        installed_ids = await self.character_client.get_installed_furniture_item_ids()
        if inventory_item.id in installed_ids:
            raise ValidationError(
                field="inventory_item_id",
                message="Предмет установлен в доме — сначала снимите его оттуда.",
            )
        
        # 2. Получаем информацию о персонаже (вес и локация)
        character = await self.character_client.get_character_weight_balance(character_id)
        
        # 3. Исключение: в trade-hall можно перемещать предметы из forge и jewelers
        TRADE_HALL_SLUG = "1.27.trade-hall"
        EQUIPMENT_LOCATIONS = {"1.13.forge", "1.16.jewelers"}

        is_trade_hall = character.location_slug == TRADE_HALL_SLUG
        item_from_equipment = inventory_item.item.location_slug in EQUIPMENT_LOCATIONS

        if not (character.location_slug == inventory_item.item.location_slug or 
                (is_trade_hall and item_from_equipment)):
            raise CharacterNotInItemLocationError(
                current_location=character.location_slug,
                required_location=inventory_item.item.location_slug
            )
                
        # 4. Получаем магазин персонажа в этой локации
        shop = await self.shop_repository.get_for_character_or_none(character_id, character.location_slug)
        
        if shop is None:
            raise ModelFieldNotFoundException(
                model=type(shop),
                field="character_id, location_slug",
                value=f"{character_id}, {character.location_slug}"
            )
        
        # 5. Получаем настройки магазина
        shop_settings = await self.shop_settings_repository.get_by_location_and_level(
            shop.location_slug,
            shop.level
        )

        # 5.1 Лицензия нужна только для ТОРГОВЛИ (выставления на продажу), не для хранения.
        if shop.location_slug == "1.27.trade-hall":
            allowed_types = {
                ItemType.WEAPON,
                ItemType.SHIELD,
                ItemType.HELMET,
                ItemType.ARMOR,
                ItemType.GAUNTLETS,
                ItemType.GLOVES,
                ItemType.LEGGINGS,
                ItemType.BOOTS,
                ItemType.CLOAK,
                ItemType.AMULET,
                ItemType.PENDANT,
                ItemType.RING,
                ItemType.KIT,
            }

            if inventory_item.item.item_type not in allowed_types:
                raise ValidationError(field='item_type', message='Item type not allowed in trade tent')

            if not inventory_item.item.can_sell:
                raise ValidationError(field='can_sell', message='Item not allowed to be sold')
        
        # 6. Проверка количества
        if amount < 1 or amount > inventory_item.amount:
            raise ValidationError(field="amount", message=f"Cannot move {amount}. Available: {inventory_item.amount}")
        
        # 7. Рассчитываем дополнительный вес
        additional_weight = inventory_item.item.weight * amount
        
        # 8. ✅ НОВАЯ ЛОГИКА: Проверка вместимости с автоматическим усечением для стакабельных
        if shop.current_capacity + additional_weight > shop_settings.capacity:
            if inventory_item.item.is_stackable:
                # Вычисляем максимум, который поместится
                max_additional = shop_settings.capacity - shop.current_capacity
                max_amount = max_additional // inventory_item.item.weight if inventory_item.item.weight > 0 else 0
                
                if max_amount < 1:
                    # Нельзя переместить даже 1 штуку
                    raise ShopCapacityExceededError(
                        current_capacity=shop.current_capacity,
                        max_capacity=shop_settings.capacity,
                        location_slug=shop.location_slug,
                    )
                
                # Тихое усечение: перемещаем максимум возможного
                amount = max_amount
                additional_weight = inventory_item.item.weight * amount
            else:
                # Нестакабельный предмет не помещается → ошибка
                raise ShopCapacityExceededError(
                    current_capacity=shop.current_capacity,
                    max_capacity=shop_settings.capacity,
                    location_slug=shop.location_slug,
                )
        
        # 9. Переносим item из инвентаря в магазин
        if amount == inventory_item.amount:
            await self.character_item_repository.transfer_item_to_shop(
                item_id=item_id,
                shop_id=shop.id
            )
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(item_id)
        else:
            new_item_id = await self.character_item_repository.split_amount(
                inventory_item_id=item_id,
                amount=amount
            )
            await self.character_item_repository.transfer_item_to_shop(
                item_id=new_item_id,
                shop_id=shop.id
            )
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(new_item_id)

        # 🆕 НОВОЕ: Публикуем событие
        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "shop_item_added",
                    "item_id": str(item_id),
                    "shop_id": str(shop.id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish economy event: %s", e)        
        
        # 10. Пересчёт веса персонажа
        new_weight = await self.character_item_repository.get_total_weight(character_id)
        await self.character_client.update_weight(character_id, float(new_weight))
        
        # 11. Пересчитываем capacity из фактического содержимого
        await self.shop_repository.recalculate_capacity(shop.id)
        
        # 12. Возвращаем сгруппированные items из локации
        return await self.character_item_service.get_items_from_location(character_id)

    async def withdraw_item_from_shop(
        self: Self,
        character_id: uuid.UUID,
        item_id: uuid.UUID,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        # 1. Получаем InventoryItem по ID с подгрузкой Item
        inventory_item = await self.character_item_repository.get_by_id(item_id)
        
        # 2. Получаем информацию о персонаже (вес и локация)
        character = await self.character_client.get_character_weight_balance(character_id)
        
        # 3. Исключение: в trade-hall можно перемещать предметы из forge и jewelers
        TRADE_HALL_SLUG = "1.27.trade-hall"
        EQUIPMENT_LOCATIONS = {"1.13.forge", "1.16.jewelers"}

        is_trade_hall = character.location_slug == TRADE_HALL_SLUG
        item_from_equipment = inventory_item.item.location_slug in EQUIPMENT_LOCATIONS

        if not (character.location_slug == inventory_item.item.location_slug or 
                (is_trade_hall and item_from_equipment)):
            raise CharacterNotInItemLocationError(
                current_location=character.location_slug,
                required_location=inventory_item.item.location_slug
            )
        
        # 4. Получаем магазин персонажа в этой локации
        shop = await self.shop_repository.get_for_character_or_none(character_id, character.location_slug)
        
        if shop is None:
            raise ModelFieldNotFoundException(
                model=type(shop),
                field="character_id, location_slug",
                value=f"{character_id}, {character.location_slug}"
            )
        
        # 5. Проверка количества
        if amount < 1 or amount > inventory_item.amount:
            raise ValidationError(field="amount", message=f"Cannot withdraw {amount}. Available: {inventory_item.amount}")
        
        # 6. Рассчитываем вес предмета
        item_weight = inventory_item.item.weight * amount
        
        # ✅ НОВАЯ ЛОГИКА: Проверка веса с автоматическим усечением для стакабельных
        if character.weight + item_weight > character.max_weight:
            if inventory_item.item.is_stackable:
                # Вычисляем максимум, который поместится
                max_additional = character.max_weight - character.weight
                max_amount = max_additional // inventory_item.item.weight if inventory_item.item.weight > 0 else 0
                
                if max_amount < 1:
                    # Нельзя переместить даже 1 штуку
                    raise CharacterWeightExceededError(
                        current_weight=int(character.weight),
                        max_weight=int(character.max_weight),
                    )
                
                # Тихое усечение: перемещаем максимум возможного
                amount = max_amount
                item_weight = inventory_item.item.weight * amount
            else:
                # Нестакабельный предмет не помещается → ошибка
                raise CharacterWeightExceededError(
                    current_weight=int(character.weight),
                    max_weight=int(character.max_weight),
                )
        
        # ✅ НОВОЕ: Проверка веса персонажа перед забором из лавки
        if character.weight + item_weight > character.max_weight:
            raise CharacterWeightExceededError(
                current_weight=int(character.weight),
                max_weight=int(character.max_weight),
            )
        
        # 7. Переносим item из магазина в инвентарь персонажа
        if amount == inventory_item.amount:
            await self.character_item_repository.withdraw_item_from_shop(
                item_id=item_id,
                character_id=character_id
            )
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(item_id)
        else:
            new_item_id = await self.character_item_repository.split_amount(
                inventory_item_id=item_id,
                amount=amount
            )
            await self.character_item_repository.withdraw_item_from_shop(
                item_id=new_item_id,
                character_id=character_id
            )
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(new_item_id)

        # 🆕 НОВОЕ: Публикуем событие
        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "shop_item_removed",
                    "item_id": str(item_id),
                    "shop_id": str(shop.id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish economy event: %s", e)        
        
        # 8. Пересчёт веса персонажа
        new_weight = await self.character_item_repository.get_total_weight(character_id)
        await self.character_client.update_weight(character_id, float(new_weight))
        
        # 9. Пересчитываем capacity из фактического содержимого
        await self.shop_repository.recalculate_capacity(shop.id)
        
        # 10. Возвращаем сгруппированные items из локации
        return await self.character_item_service.get_items_from_location(character_id)