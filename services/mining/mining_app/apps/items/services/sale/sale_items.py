import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, Self

from ....resources.events.publisher import RedisPublisherProtocol
from ...adapters.characters import CharacterServiceClientProtocol
from ...enums import ItemType
from ...exceptions import CityTradingShopLicenseExpiredError
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.sale.sale_inventory_items import (
    SaleInventoryItemRepositoryProtocol,
)
from ...schemas import LocationItemsGroupedSchema
from ...utils.price_validation import validate_sale_price
from ..character.character_items import CharacterItemServiceProtocol

logger = logging.getLogger(__name__)


class SaleItemServiceProtocol(Protocol):
    async def add_item_to_sale(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        ...

    async def remove_item_from_sale(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        amount: int | None = None
    ) -> LocationItemsGroupedSchema:
        ...

    async def update_sale_price(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        price: Decimal
    ) -> LocationItemsGroupedSchema:
        ...


class SaleItemService(SaleItemServiceProtocol):
    def __init__(
        self: Self,
        sale_repository: SaleInventoryItemRepositoryProtocol,
        character_item_repository: CharacterItemRepositoryProtocol,
        character_item_service: CharacterItemServiceProtocol,
        shop_repository: CityTradingShopCharacterRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        redis_publisher: RedisPublisherProtocol, 
    ):
        self.sale_repository = sale_repository
        self.character_item_repository = character_item_repository
        self.character_item_service = character_item_service
        self.shop_repository = shop_repository
        self.character_client = character_client
        self.redis_publisher = redis_publisher 
    async def add_item_to_sale(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        # 1. Получаем InventoryItem по ID
        inventory_item = await self.character_item_repository.get_by_id(inventory_item_id)
        # ═══ ЭСКРОУ: предмет в сделке «заморожен» — продавать нельзя ═══
        if getattr(inventory_item, "deal_id", None) is not None:
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                field="deal_id",
                message="Предмет находится в сделке — сначала уберите его из сделки.",
            )
        validate_sale_price(inventory_item.item.price, price)
        
        # 2. Проверяем, что shop_id не null
        if inventory_item.shop_id is None:
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                message="Item must be in shop to be listed for sale",
                field="shop_id"
            )
        # 2.1. Проверяем статус лицензии магазина
        shop = await self.shop_repository.get(inventory_item.shop_id)

        # Лицензия проверяется для всех торговых точек
        if shop.end_license is None or shop.end_license < datetime.now(UTC):
            raise CityTradingShopLicenseExpiredError(
                location_slug=shop.location_slug,
                end_license=str(shop.end_license)
            )

        if shop.location_slug == "1.27.trade-hall":

            # Проверяем тип предмета и can_sell
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
        
        # 3. Получаем владельца магазина через shop_id
        shop_owner_id = await self.sale_repository.get_shop_owner_by_inventory_item(inventory_item_id)
        
        # 4. Проверяем, что владелец магазина = текущему персонажу
        if shop_owner_id != character_id:
            from shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError(
                detail="You don't own this shop",
                extras={"shop_owner_id": str(shop_owner_id), "character_id": str(character_id)}
            )
        
        # 5. Проверяем количество
        if amount < 1 or amount > inventory_item.amount:
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                field="amount",
                message=f"Cannot sell {amount}. Available: {inventory_item.amount}"
            )

        # 5.1. Проверяем, что item ещё не в продаже
        if await self.sale_repository.exists(inventory_item_id):
            from .....core.utils.exceptions import ModelAlreadyExistsError
            from ...models import SaleInventoryItem
            raise ModelAlreadyExistsError(
                model=SaleInventoryItem,
                field="inventory_item_id",
                message=f"Item {inventory_item_id} is already listed for sale"
            )

        # 6. Создаём запись о продаже
        if amount == inventory_item.amount:
            # целиком — продаём исходную строку
            await self.sale_repository.create(inventory_item_id, price)
        else:
            # часть — отделяем новую строку-партию и продаём её
            new_inventory_item_id = await self.character_item_repository.split_amount(
                inventory_item_id, amount
            )
            await self.sale_repository.create(new_inventory_item_id, price)

        # 🆕 НОВОЕ: Публикуем событие
        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "sale_item_created",
                    "inventory_item_id": str(inventory_item_id),
                    "shop_id": str(inventory_item.shop_id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish economy event: %s", e)    

        # 7. Возвращаем сгруппированные items из локации
        return await self.character_item_service.get_items_from_location(character_id)

    async def remove_item_from_sale(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        amount: int | None = None
    ) -> LocationItemsGroupedSchema:
        # 1. Получаем InventoryItem по ID
        inventory_item = await self.character_item_repository.get_by_id(inventory_item_id)

        # 2. Проверяем, что shop_id не null
        if inventory_item.shop_id is None:
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                detail="Item must be in shop",
                field="shop_id"
            )

        # 🆕 ДОБАВИТЬ: Загружаем shop для получения location_slug
        shop = await self.shop_repository.get(inventory_item.shop_id)

        # 3. Получаем владельца магазина через shop_id
        shop_owner_id = await self.sale_repository.get_shop_owner_by_inventory_item(inventory_item_id)

        # 4. Проверяем, что владелец магазина = текущему персонажу
        if shop_owner_id != character_id:
            from shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError(
                detail="You don't own this shop",
                extras={"shop_owner_id": str(shop_owner_id), "character_id": str(character_id)}
            )

        # 5. Проверяем количество
        if amount is not None and (amount < 1 or amount > inventory_item.amount):
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                field="amount",
                message=f"Cannot withdraw {amount}. On sale: {inventory_item.amount}"
            )

        if amount is None or amount >= inventory_item.amount:
            # ЗАБРАТЬ ВСЁ: снимаем с продажи, строка остаётся в лавке
            await self.sale_repository.delete(inventory_item_id)
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(inventory_item_id)
        else:
            # ЗАБРАТЬ ЧАСТЬ: отделяем amount в новую строку, оставляем в лавке,
            # остальное остаётся на продаже по той же цене
            new_item_id = await self.character_item_repository.split_amount(
                inventory_item_id, amount
            )
            if inventory_item.item.is_stackable:
                await self.character_item_repository.merge_identical_stack(new_item_id)

        # 🆕 НОВОЕ: Публикуем событие
        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "sale_item_removed",
                    "inventory_item_id": str(inventory_item_id),
                    "shop_id": str(inventory_item.shop_id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish economy event: %s", e)        

        # 6. Возвращаем сгруппированные items из локации
        return await self.character_item_service.get_items_from_location(character_id)

    async def update_sale_price(
        self: Self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        price: Decimal
    ) -> LocationItemsGroupedSchema:
        # 1. Получаем InventoryItem по ID
        inventory_item = await self.character_item_repository.get_by_id(inventory_item_id)                
        validate_sale_price(inventory_item.item.price, price)

        # 2. Проверяем, что предмет в лавке
        if inventory_item.shop_id is None:
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(field="shop_id", message="Item must be in shop")

        # 2.1. ✅ НОВОЕ: Проверяем статус лицензии магазина перед изменением цены
        shop = await self.shop_repository.get(inventory_item.shop_id)
        if shop.end_license is None or shop.end_license < datetime.now(UTC):
            raise CityTradingShopLicenseExpiredError(
                location_slug=shop.location_slug,
                end_license=str(shop.end_license)
            )

        # 3. Проверяем владельца
        shop_owner_id = await self.sale_repository.get_shop_owner_by_inventory_item(inventory_item_id)
        if shop_owner_id != character_id:
            from shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError(
                detail="You don't own this shop",
                extras={"shop_owner_id": str(shop_owner_id), "character_id": str(character_id)}
            )

        # 4. Проверяем, что предмет действительно на продаже
        if not await self.sale_repository.exists(inventory_item_id):
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(field="inventory_item_id", message="Item is not on sale")

        # 5. Обновляем цену
        await self.sale_repository.update_price(inventory_item_id, price)

        # 🆕 НОВОЕ: Публикуем событие
        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "sale_price_updated",
                    "inventory_item_id": str(inventory_item_id),
                    "shop_id": str(inventory_item.shop_id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish economy event: %s", e)

        # 6. Возвращаем сгруппированные items
        return await self.character_item_service.get_items_from_location(character_id)
