import uuid
from datetime import UTC, datetime

from ...items.adapters.characters import CharacterServiceClientProtocol
from ...items.enums import ItemType
from ..repositories.admin_read import AdminReadRepository
from ..schemas import (
    ITEM_TYPE_LABELS,
    RESOURCE_CATEGORY_LABELS,
    AdminCharacterDetailsSchema,
    AdminCharacterListSchema,
    AdminCharacterResourceSchema,
    AdminCharacterSchema,
    AdminInventoryGroupsSchema,
    AdminInventoryItemSchema,
    AdminItemCatalogListSchema,
    AdminItemCatalogSchema,
    AdminItemTypeSchema,
    AdminResourceCategorySchema,
    AdminResourceListSchema,
    AdminResourceSchema,
)


class AdminReadService:
    def __init__(self, repository: AdminReadRepository, characters: CharacterServiceClientProtocol):
        self.repository = repository
        self.characters = characters

    async def list_characters(self, search: str | None, limit: int, offset: int) -> AdminCharacterListSchema:
        result = await self.characters.search_characters(search, limit, offset)
        return AdminCharacterListSchema(
            objects=[AdminCharacterSchema.model_validate(character.model_dump()) for character in result.objects],
            count=result.count,
        )

    async def get_character(self, character_id: uuid.UUID) -> AdminCharacterDetailsSchema:
        character = await self.characters.get_full_character(character_id)
        return AdminCharacterDetailsSchema(
            id=character.id, name=character.name, level=character.level,
            location_slug=character.location_slug, is_online=character.is_online,
            ducats=character.ducats, gold=character.gold,
        )

    async def get_inventory(self, character_id: uuid.UUID) -> AdminInventoryGroupsSchema:
        groups = AdminInventoryGroupsSchema(inventory=[], shop=[], sale=[], deals=[])
        now = datetime.now(UTC)
        for inventory_item, sale_price, equipment_id in await self.repository.get_character_inventory(character_id):
            result = AdminInventoryItemSchema(
                id=inventory_item.id, item_slug=inventory_item.item_slug, item_name=inventory_item.item.name,
                item_type=inventory_item.item.item_type, amount=inventory_item.amount, wear=inventory_item.wear,
                expired_date=inventory_item.expired_date,
                is_expired=inventory_item.expired_date is not None and inventory_item.expired_date < now,
                is_equipped=equipment_id is not None, deal_id=inventory_item.deal_id,
                shop_id=inventory_item.shop_id, sale_price=sale_price,
            )
            if inventory_item.deal_id is not None:
                groups.deals.append(result)
            elif sale_price is not None:
                groups.sale.append(result)
            elif inventory_item.shop_id is not None:
                groups.shop.append(result)
            else:
                groups.inventory.append(result)
        return groups

    async def get_character_resources(self, character_id: uuid.UUID) -> list[AdminCharacterResourceSchema]:
        return [
            AdminCharacterResourceSchema(resource_slug=resource.slug, resource_name=resource.name, category=resource.category, amount=balance.amount)
            for balance, resource in await self.repository.get_character_resources(character_id)
        ]

    async def list_items(self, item_type: ItemType | None, location_slug: str | None, search: str | None, limit: int, offset: int) -> AdminItemCatalogListSchema:
        items, count = await self.repository.list_items(item_type, location_slug, search, limit, offset)
        return AdminItemCatalogListSchema(objects=[AdminItemCatalogSchema.model_validate(item) for item in items], count=count)

    async def list_resources(self, category: str | None, search: str | None, limit: int, offset: int) -> AdminResourceListSchema:
        resources, count = await self.repository.list_resources(category, search, limit, offset)
        return AdminResourceListSchema(objects=[AdminResourceSchema.model_validate(resource) for resource in resources], count=count)

    async def item_types(self) -> list[AdminItemTypeSchema]:
        return [
            AdminItemTypeSchema(
                item_type=item_type,
                readable_name=ITEM_TYPE_LABELS.get(item_type, item_type.name),
            )
            for item_type in ItemType
        ]

    async def resource_categories(self) -> list[AdminResourceCategorySchema]:
        return [
            AdminResourceCategorySchema(category=category, readable_name=RESOURCE_CATEGORY_LABELS.get(category, category))
            for category in await self.repository.get_resource_categories()
        ]
