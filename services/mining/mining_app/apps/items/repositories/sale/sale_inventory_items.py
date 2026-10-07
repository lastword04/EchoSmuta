import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, Self

import sqlalchemy as sa

from .....core.db import AsyncSession
from ...models import CityTradingShop, InventoryItem, Item, SaleInventoryItem
from ...schemas import SaleInventoryItemReadSchema


class SaleInventoryItemRepositoryProtocol(Protocol):
    async def create(self: Self, inventory_item_id: uuid.UUID, price: Decimal) -> SaleInventoryItemReadSchema:
        """Создаёт запись о продаже item."""
        ...

    async def delete(self: Self, inventory_item_id: uuid.UUID) -> None:
        """Удаляет запись о продаже item."""
        ...

    async def get_shop_owner_by_inventory_item(self: Self, inventory_item_id: uuid.UUID) -> uuid.UUID | None:
        """Получает character_id владельца магазина по inventory_item_id."""
        ...

    async def get_sale_items_by_shop(self: Self, shop_id: uuid.UUID) -> list[SaleInventoryItemReadSchema]:
        """Получает все items на продаже в магазине."""
        ...

    async def exists(self: Self, inventory_item_id: uuid.UUID) -> bool:
        """Проверяет, существует ли запись о продаже для данного inventory_item_id."""
        ...

    async def get_sale_item_with_details(self: Self, inventory_item_id: uuid.UUID) -> tuple[SaleInventoryItemReadSchema, uuid.UUID, int] | None:
        """Получает sale item с shop_id и весом товара. Возвращает (sale_item, shop_id, item_weight) или None."""
        ...

    async def update_price(self: Self, inventory_item_id: uuid.UUID, price: Decimal) -> None:
        """Меняет цену товара на продаже."""
        ...


class SaleInventoryItemRepository(SaleInventoryItemRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def create(self: Self, inventory_item_id: uuid.UUID, price: Decimal) -> SaleInventoryItemReadSchema:
        async with self.session as s:
            stmt_insert = (
                sa.insert(SaleInventoryItem)
                .values(inventory_item_id=inventory_item_id, price=price)
                .returning(SaleInventoryItem.id)
            )
            result = await s.execute(stmt_insert)
            sale_item_id = result.scalar_one()
            await s.commit()
            
            stmt_select = (
                sa.select(
                    SaleInventoryItem.id,
                    SaleInventoryItem.inventory_item_id,
                    SaleInventoryItem.price,
                    SaleInventoryItem.created_at,
                    SaleInventoryItem.updated_at,
                    Item.name.label('item_name'),
                    Item.ability_parameters,
                    Item.parameters,
                    Item.item_type,
                    Item.minimal_level,
                    Item.price.label('item_price'),   
                    Item.weight.label('weight'),    
                    InventoryItem.character_id,
                    InventoryItem.shop_id,
                    InventoryItem.item_slug,
                    InventoryItem.amount,
                    InventoryItem.expired_date,
                    InventoryItem.used_count,
                    InventoryItem.wear
                )
                .select_from(SaleInventoryItem)
                .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(SaleInventoryItem.id == sale_item_id)
            )
            
            result_select = await s.execute(stmt_select)
            row = result_select.one()
            
            return SaleInventoryItemReadSchema(
                id=row.id,
                inventory_item_id=row.inventory_item_id,
                price=row.price,
                created_at=row.created_at,
                updated_at=row.updated_at,
                item_name=row.item_name,
                ability_parameters=row.ability_parameters,
                parameters=row.parameters,
                item_type=row.item_type,
                minimal_level=row.minimal_level,
                item_price=row.item_price,     
                weight=row.weight,            
                character_id=row.character_id,
                shop_id=row.shop_id,
                item_slug=row.item_slug,
                amount=row.amount,
                expired_date=row.expired_date,
                used_count=row.used_count,
                wear=row.wear
            )

    async def delete(self: Self, inventory_item_id: uuid.UUID) -> None:
        """Удаляет запись о продаже item."""
        async with self.session as s:
            stmt_delete = (
                sa.delete(SaleInventoryItem)
                .where(SaleInventoryItem.inventory_item_id == inventory_item_id)
            )
            
            await s.execute(stmt_delete)
            await s.commit()

    async def get_shop_owner_by_inventory_item(self: Self, inventory_item_id: uuid.UUID) -> uuid.UUID | None:
        """Получает character_id владельца магазина по inventory_item_id."""
        async with self.session as s:
            stmt = (
                sa.select(CityTradingShop.character_id)
                .select_from(InventoryItem)
                .join(CityTradingShop, InventoryItem.shop_id == CityTradingShop.id)
                .where(InventoryItem.id == inventory_item_id)
            )
            
            result = await s.execute(stmt)
            character_id = result.scalar_one_or_none()
            
            return character_id

    async def get_sale_items_by_shop(self: Self, shop_id: uuid.UUID) -> list[SaleInventoryItemReadSchema]:
        async with self.session as s:
            stmt = (
                sa.select(
                    SaleInventoryItem.id,
                    SaleInventoryItem.inventory_item_id,
                    SaleInventoryItem.price,
                    SaleInventoryItem.created_at,
                    SaleInventoryItem.updated_at,
                    Item.name.label('item_name'),
                    Item.ability_parameters,                    
                    Item.parameters,      
                    Item.item_type,         
                    Item.minimal_level,
                    Item.price.label('item_price'),   
                    Item.weight.label('weight'),      
                    InventoryItem.character_id,
                    InventoryItem.shop_id,
                    InventoryItem.item_slug,
                    InventoryItem.amount,
                    InventoryItem.expired_date,
                    InventoryItem.used_count,
                    InventoryItem.wear
                )
                .select_from(SaleInventoryItem)
                .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.shop_id == shop_id,
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > datetime.now(UTC)
                    )
                )
                .order_by(SaleInventoryItem.created_at.desc())
            )
            
            result = await s.execute(stmt)
            rows = result.all()
            
            return [
                SaleInventoryItemReadSchema(
                    id=row.id,
                    inventory_item_id=row.inventory_item_id,
                    price=row.price,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    item_name=row.item_name,
                    ability_parameters=row.ability_parameters,
                    parameters=row.parameters,      
                    item_type=row.item_type,         
                    minimal_level=row.minimal_level,
                    item_price=row.item_price,       
                    weight=row.weight,              
                    character_id=row.character_id,
                    shop_id=row.shop_id,
                    item_slug=row.item_slug,
                    amount=row.amount,
                    expired_date=row.expired_date,
                    used_count=row.used_count,
                    wear=row.wear,
                )
                for row in rows
            ]

    async def exists(self: Self, inventory_item_id: uuid.UUID) -> bool:
        """Проверяет, существует ли запись о продаже для данного inventory_item_id."""
        async with self.session as s:
            stmt = (
                sa.select(sa.func.count())
                .select_from(SaleInventoryItem)
                .where(SaleInventoryItem.inventory_item_id == inventory_item_id)
            )
            
            result = await s.execute(stmt)
            count = result.scalar_one()
            
            return count > 0

    async def get_sale_item_with_details(self: Self, inventory_item_id: uuid.UUID) -> tuple[SaleInventoryItemReadSchema, uuid.UUID, int] | None:
        async with self.session as s:
            stmt = (
                sa.select(
                    SaleInventoryItem.id,
                    SaleInventoryItem.inventory_item_id,
                    SaleInventoryItem.price,
                    SaleInventoryItem.created_at,
                    SaleInventoryItem.updated_at,
                    Item.name.label('item_name'),
                    Item.ability_parameters,
                    Item.parameters,
                    Item.item_type,
                    Item.minimal_level,
                    Item.price.label('item_price'),        
                    Item.weight.label('item_weight'),     
                    Item.weight.label('weight'),           
                    InventoryItem.character_id,
                    InventoryItem.shop_id,
                    InventoryItem.item_slug,
                    InventoryItem.amount,
                    InventoryItem.expired_date,
                    InventoryItem.used_count,
                    InventoryItem.wear
                )
                .select_from(SaleInventoryItem)
                .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(SaleInventoryItem.inventory_item_id == inventory_item_id)
            )
            
            result = await s.execute(stmt)
            row = result.one_or_none()
            
            if row is None:
                return None
            
            sale_item = SaleInventoryItemReadSchema(
                id=row.id,
                inventory_item_id=row.inventory_item_id,
                price=row.price,
                created_at=row.created_at,
                updated_at=row.updated_at,
                item_name=row.item_name,
                ability_parameters=row.ability_parameters,
                parameters=row.parameters,
                item_type=row.item_type,
                minimal_level=row.minimal_level,
                item_price=row.item_price,        
                weight=row.weight,                
                character_id=row.character_id,
                shop_id=row.shop_id,
                item_slug=row.item_slug,
                amount=row.amount,
                expired_date=row.expired_date,
                used_count=row.used_count,
                wear=row.wear
            )
            
            return sale_item, row.shop_id, row.item_weight

    async def update_price(self: Self, inventory_item_id: uuid.UUID, price: Decimal) -> None:
        """Меняет цену товара на продаже."""
        async with self.session as s:
            stmt = (
                sa.update(SaleInventoryItem)
                .where(SaleInventoryItem.inventory_item_id == inventory_item_id)
                .values(price=price)
            )
            await s.execute(stmt)
            await s.commit()
