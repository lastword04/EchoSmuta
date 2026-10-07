import uuid
from datetime import UTC, datetime
from typing import Protocol, Self

from .....core.utils.exceptions import ModelFieldNotFoundException
from ...adapters.characters import CharacterServiceClientProtocol
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.crafting_license.crafting_license import (
    CraftingLicenseRepositoryProtocol,
)
from ...repositories.sale.sale_inventory_items import (
    SaleInventoryItemRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ...schemas import (
    InventoryItemCreateSchema,
    InventoryItemReadSchema,
    LocationItemsGroupedSchema,
)


class CharacterItemServiceProtocol(Protocol):
    async def get_character_items(self: Self, character_id: uuid.UUID) -> list[InventoryItemReadSchema]:
        ...
    
    async def get_items_from_location(self: Self, character_id: uuid.UUID) -> LocationItemsGroupedSchema:
        ...
    
    async def add_item(self: Self, character_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        ...

    async def get_by_id_and_character(self: Self, inventory_item_id: uuid.UUID, character_id: uuid.UUID) -> InventoryItemReadSchema: 
        ...

    async def consume_item(self: Self, inventory_item_id: uuid.UUID) -> None: 
        ...

    async def take_item(
        self: Self,
        character_id: uuid.UUID,
        amount: int,
        inventory_item_id: uuid.UUID | None = None,
        item_slug: str | None = None,
        force: bool = False,
    ) -> None:
        ...

    async def get_total_weight(self: Self, character_id: uuid.UUID) -> int:
        ...


class CharacterItemService(CharacterItemServiceProtocol):
    def __init__(
        self: Self,
        repository: CharacterItemRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        shop_repository: CityTradingShopCharacterRepositoryProtocol,
        sale_repository: SaleInventoryItemRepositoryProtocol,
        settings_repository: CityTradingShopSettingsRepositoryProtocol,
        crafting_license_repository: CraftingLicenseRepositoryProtocol
    ):
        self.repository = repository
        self.character_client = character_client
        self.shop_repository = shop_repository
        self.sale_repository = sale_repository
        self.settings_repository = settings_repository
        self.crafting_license_repository = crafting_license_repository
    
    # ИЗМЕНЕНО: не передаём location_slug — инвентарь показывает ВСЕ предметы
    async def get_character_items(self: Self, character_id: uuid.UUID) -> list[InventoryItemReadSchema]:
        return await self.repository.get_character_items(character_id, location_slug=None)
    
    async def get_items_from_location(self: Self, character_id: uuid.UUID) -> LocationItemsGroupedSchema:
        # Получаем location_slug персонажа
        character = await self.character_client.get_simple_character_balance(character_id)

        # Пытаемся получить магазин персонажа в этой локации
        shop = None
        try:
            shop = await self.shop_repository.get_for_character(character_id, character.location_slug)
        except ModelFieldNotFoundException:
            # Магазина нет, это нормально
            pass

        shop_id = shop.id if shop else None
        shop_end_license = shop.end_license if shop else None

        # Крафтовая лицензия (для production-локаций).
        # None = записи нет (не production), False = истекла, True = активна
        crafting_license_active = None
        license = await self.crafting_license_repository.get_for_character(
            character_id, character.location_slug
        )
        if license is not None:
            crafting_license_active = license.end_date > datetime.now(UTC)

        # Получаем все items из локации (упрощенные, с item_name)
        all_items = await self.repository.get_items_from_location_simple(character_id, character.location_slug, shop_id)

        # Исключаем предметы, установленные в домах (данные — в character-service)
        installed_ids = await self.character_client.get_installed_furniture_item_ids()
        if installed_ids:
            installed_set = set(installed_ids)
            all_items = [it for it in all_items if it.id not in installed_set]

        # Получаем sale items если есть магазин
        sale_items = []
        sale_item_ids = set()
        if shop_id:
            sale_items = await self.sale_repository.get_sale_items_by_shop(shop_id)
            sale_item_ids = {sale_item.inventory_item_id for sale_item in sale_items}

        # Разделяем на группы, исключая sale items из shop_items
        character_items = []
        shop_items = []

        for item in all_items:
            if item.character_id is not None:
                character_items.append(item)
            elif item.shop_id is not None and item.id not in sale_item_ids:
                shop_items.append(item)

        # ✅ НОВОЕ: вместимость лавки
        current_capacity = 0
        max_capacity = 0
        if shop is not None:
            current_capacity = getattr(shop, "current_capacity", 0) or 0
            shop_level = getattr(shop, "level", 0)
            try:
                settings = await self.settings_repository.get_by_location_and_level(
                    character.location_slug, shop_level
                )
                max_capacity = settings.capacity or 0
            except ModelFieldNotFoundException:
                max_capacity = 0

        return LocationItemsGroupedSchema(
            character_items=character_items,
            shop_items=shop_items,
            sale_items=sale_items,
            current_capacity=current_capacity,
            max_capacity=max_capacity,
            shop_end_license=shop_end_license,
            crafting_license_active=crafting_license_active
        )
    
    async def add_item(self: Self, character_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        item = await self.repository.add_item(character_id, data)

        # Пересчёт веса после получения предмета
        new_weight = await self.repository.get_total_weight(character_id)
        await self.character_client.update_weight(character_id, float(new_weight))

        return item

    async def get_by_id_and_character(self: Self, inventory_item_id: uuid.UUID, character_id: uuid.UUID):
        return await self.repository.get_by_id_and_character(inventory_item_id, character_id)

    async def consume_item(self: Self, inventory_item_id: uuid.UUID) -> None:
        await self.repository.consume_item(inventory_item_id)

    async def take_item(
        self: Self,
        character_id: uuid.UUID,
        amount: int,
        inventory_item_id: uuid.UUID | None = None,
        item_slug: str | None = None,
        force: bool = False,
    ) -> None:
        await self.repository.take_item(
            character_id=character_id,
            amount=amount,
            inventory_item_id=inventory_item_id,
            item_slug=item_slug,
            force=force,
        )
        new_weight = await self.repository.get_total_weight(character_id)
        await self.character_client.update_weight(character_id, float(new_weight))

    async def get_total_weight(self: Self, character_id: uuid.UUID) -> int:
        return await self.repository.get_total_weight(character_id)
