import uuid
from datetime import UTC, datetime, timedelta
from typing import Self

import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import (
    ModelFieldNotFoundException,
    ModelNotFoundException,
)
from ...enums import ItemType
from ...models import CityTradingShop, InventoryItem, Item, SaleInventoryItem
from ...schemas import (
    CityTradingShopCreateSchema,
    CityTradingShopReadSchema,
    CityTradingShopUpdateInfoSchema,
    CityTradingShopUpdatePhotoSchema,
    CityTradingShopUpdateSchema,
)
from .shop_number_utils import get_next_shop_number


class CityTradingShopCharacterRepositoryProtocol(
    BaseRepositoryImpl[
        CityTradingShop,
        CityTradingShopReadSchema,
        CityTradingShopCreateSchema,
        CityTradingShopUpdateSchema
    ]
):
    async def get_for_character(self, character_id: uuid.UUID, location_slug: str) -> CityTradingShopReadSchema:
        ...

    async def get_for_character_or_none(self, character_id: uuid.UUID, location_slug: str) -> CityTradingShopReadSchema | None:
        """Получает магазин персонажа в локации или None если не найден."""

    async def get_by_location_and_character(self, location_slug: str, character_id: uuid.UUID) -> CityTradingShopReadSchema | None:
        """Получает магазин по локации и персонажу или None если не найден."""

    async def get_by_number(self, location_slug: str, number: int) -> CityTradingShopReadSchema:
        ...

    async def update_info(self, id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        ...

    async def update_photo(self, id: uuid.UUID, photo_schema: CityTradingShopUpdatePhotoSchema, character_id: uuid.UUID) -> bool:
        ...

    async def update_license_duration(
        self,
        id: uuid.UUID,
        character_id: uuid.UUID,
        duration: timedelta
    ) -> CityTradingShopReadSchema:
        ...

    async def update_current_capacity(self, shop_id: uuid.UUID, additional_capacity: int) -> CityTradingShopReadSchema:
        ...

    async def update_shop_level(self, shop_id: uuid.UUID, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        """Увеличивает уровень магазина на 1."""

    async def get_shops_with_sale_items_paginated(
        self,
        location_slug: str,
        page: int,
        page_size: int,
        item_name: str | None = None, 
        number: int | None = None,  
        minimal_level: int | None = None,
        item_kind: str | None = None,
    ) -> tuple[list[dict], int]:
        """Получает магазины с товарами на продаже с пагинацией.
        
        Returns:
            tuple: (список магазинов с товарами, общее количество магазинов)
        """

    async def recalculate_capacity(self: Self, shop_id: uuid.UUID) -> None:
        ...


def _item_kind_condition(kind: str):
    """SQL-условие на Item по значению фильтра kind с фронтенда."""
    if kind == 'swords':
        return sa.and_(
            Item.item_type == ItemType.WEAPON,
            ~Item.slug.like('%axe-%'),
            ~Item.slug.like('%hammer-%'),
        )
    if kind == 'axes':
        return sa.and_(Item.item_type == ItemType.WEAPON, Item.slug.like('%axe-%'))
    if kind == 'hammers':
        return sa.and_(Item.item_type == ItemType.WEAPON, Item.slug.like('%hammer-%'))
    if kind == 'shields':
        return Item.item_type == ItemType.SHIELD
    if kind == 'kit':
        return Item.slug.like('%-kit')
    if kind == 'armor':
        return sa.and_(Item.item_type == ItemType.ARMOR, ~Item.slug.like('%-kit'))
    return Item.item_type == kind

class CityTradingShopCharacterRepository(CityTradingShopCharacterRepositoryProtocol):
    async def create(self, data: CityTradingShopCreateSchema) -> CityTradingShopReadSchema:
        """
        Создает новый магазин с автоматической генерацией уникального номера для локации.
        
        Переопределяет базовый метод create для добавления логики генерации номера.
        """
        async with self.session as session, session.begin():
            # Атомарно получаем следующий номер для локации
            next_number = await get_next_shop_number(session, data.location_slug)
            
            # Создаем магазин с полученным номером
            model_data = data.model_dump()
            model_data['number'] = next_number
            
            model = self.model_type(**model_data)
            session.add(model)
            await session.flush()
            await session.refresh(model)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)
    
    async def get_for_character(self, character_id: uuid.UUID, location_slug: str) -> CityTradingShopReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.location_slug == location_slug)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "character_id, location_slug", character_id)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def get_for_character_or_none(self, character_id: uuid.UUID, location_slug: str) -> CityTradingShopReadSchema | None:
        """Получает магазин персонажа в локации или None если не найден."""
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.location_slug == location_slug)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                return None
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def get_by_location_and_character(self, location_slug: str, character_id: uuid.UUID) -> CityTradingShopReadSchema | None:
        """Получает магазин по локации и персонажу или None если не найден."""
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.location_slug == location_slug,
                    self.model_type.character_id == character_id
                )
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                return None
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def get_by_number(self, location_slug: str, number: int) -> CityTradingShopReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.number == number,
                       self.model_type.location_slug == location_slug)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "number", number)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def update_info(self,  id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.id == id
                       )
                .values(update_schema.model_dump())
                .returning(self.model_type)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, id)

            
            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def update_photo(self, id: uuid.UUID, photo_schema: CityTradingShopUpdatePhotoSchema, character_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.id == id
                       )
                .values(photo_schema.model_dump())
                .returning(self.model_type)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, id)

            
            return self.read_schema_type.model_validate(model, from_attributes=True)


    async def update_license_duration(
        self,
        id: uuid.UUID,
        character_id: uuid.UUID,
        duration: timedelta
    ) -> CityTradingShopReadSchema:
        """
        Обновляет время окончания лицензии магазина с логикой:
        - Если текущая лицензия истекла или не установлена: end_license = now() + duration
        - Иначе: end_license = текущее_значение + duration
        """
        async with self.session as session, session.begin():
            # Получаем текущую запись с блокировкой для предотвращения гонок условий
            select_stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.id == id,
                    self.model_type.character_id == character_id,
                )
                .with_for_update()  # Блокировка строки для атомарности операции
            )
            
            result = await session.execute(select_stmt)
            model = result.scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, id)

            
            # Используем UTC время для согласованности с базой данных
            now = datetime.now(UTC)
            current_end = model.end_license
            
            # Логика определения нового времени окончания лицензии
            if current_end is None or current_end < now:
                new_end = now + duration
            else:
                new_end = current_end + duration
            
            # Атомарное обновление
            update_stmt = (
                sa.update(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.id == id
                )
                .values(end_license=new_end)
                .returning(self.model_type)
            )
            
            updated_result = await session.execute(update_stmt)
            updated_model = updated_result.scalar_one_or_none()
            
            return self.read_schema_type.model_validate(updated_model, from_attributes=True)

    async def update_current_capacity(self, shop_id: uuid.UUID, additional_capacity: int) -> CityTradingShopReadSchema:
        """
        Обновляет current_capacity магазина, добавляя additional_capacity к текущему значению.
        """
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == shop_id)
                .values(current_capacity=self.model_type.current_capacity + additional_capacity)
                .returning(self.model_type)
            )
            
            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, shop_id)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def update_shop_level(self, shop_id: uuid.UUID, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        """
        Увеличивает уровень магазина на 1.
        """
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(
                    self.model_type.id == shop_id,
                    self.model_type.character_id == character_id
                )
                .values(level=self.model_type.level + 1)
                .returning(self.model_type)
            )
            
            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, shop_id)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)


    async def get_shops_with_sale_items_paginated(
        self,
        location_slug: str,
        page: int,
        page_size: int,
        item_name: str | None = None,
        number: int | None = None,
        minimal_level: int | None = None,
        item_kind: str | None = None,
    ) -> tuple[list[dict], int]:
        """Получает магазины с товарами на продаже с пагинацией.

        item_name: если передан — возвращаются только магазины, у которых
                   в продаже есть товар с таким названием (в sale_items
                   попадают только эти товары).
        number:    если передан — фильтр по номеру магазина.
        """
        async with self.session as session:
             # Фильтруем только активные магазины (end_license > now)
            now = datetime.now(UTC)

            # Условия по товарам из фильтров (уровень / тип)
            item_conditions = []
            if minimal_level is not None:
                item_conditions.append(Item.minimal_level == minimal_level)
            if item_kind:
                item_conditions.append(_item_kind_condition(item_kind))
                           
                
            # Подзапрос для получения товаров на продаже для каждого магазина
            sale_items_subquery = (
                sa.select(
                    SaleInventoryItem.id.label('sale_id'),
                    SaleInventoryItem.inventory_item_id,
                    SaleInventoryItem.price,
                    SaleInventoryItem.created_at.label('sale_created_at'),
                    InventoryItem.item_slug,
                    InventoryItem.amount,
                    InventoryItem.expired_date,
                    InventoryItem.used_count,
                    InventoryItem.wear,
                    InventoryItem.shop_id,
                    Item.name.label('item_name'),
                    Item.ability_parameters.label('ability_parameters'),
                    Item.parameters.label('parameters'),
                    Item.item_type.label('item_type'),
                    Item.minimal_level.label('minimal_level'),
                )
                .select_from(SaleInventoryItem)
                .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > datetime.now(UTC)
                    )
                )
            )
            if item_conditions:
                sale_items_subquery = sale_items_subquery.where(sa.and_(*item_conditions))
            sale_items_subquery = sale_items_subquery.subquery()      
          

            conditions = [
                self.model_type.location_slug == location_slug,
                self.model_type.end_license != None,
                self.model_type.end_license > now,
                # Магазин должен иметь хотя бы 1 активный товар на продаже
                sa.exists(
                    sa.select(SaleInventoryItem.id)
                    .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                    .where(
                        InventoryItem.shop_id == self.model_type.id,
                        sa.or_(
                            InventoryItem.expired_date == None,
                            InventoryItem.expired_date > now,
                        )
                    )
                ),
            ]
            
            if item_conditions:
                # лавка видна, только если есть товар, подходящий под фильтр
                conditions.append(
                    sa.exists(
                        sa.select(SaleInventoryItem.id)
                        .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                        .join(Item, InventoryItem.item_slug == Item.slug)
                        .where(InventoryItem.shop_id == self.model_type.id)
                        .where(sa.and_(*item_conditions))
                    )
                )
            else:
                has_sale_items = sa.exists(
                    sa.select(SaleInventoryItem.id)
                    .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                    .where(InventoryItem.shop_id == self.model_type.id)
                )
                conditions.append(has_sale_items)

            # ← НОВОЕ: фильтр по номеру лавки
            if number is not None:
                conditions.append(self.model_type.number == number)

            # ← НОВОЕ: фильтр по товару — только магазины, где он продаётся
            if item_name:
                shops_with_item_subquery = (
                    sa.select(InventoryItem.shop_id)
                    .select_from(SaleInventoryItem)
                    .join(InventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
                    .join(Item, InventoryItem.item_slug == Item.slug)
                    .where(Item.name == item_name)
                )
                conditions.append(self.model_type.id.in_(shops_with_item_subquery))

            # Общее количество магазинов С УЧЁТОМ фильтров
            count_stmt = (
                sa.select(sa.func.count())
                .select_from(self.model_type)
                .where(*conditions)
            )
            total_count = (await session.execute(count_stmt)).scalar_one()

            # Получаем активные магазины с пагинацией
            offset = (page - 1) * page_size
            shops_stmt = (
                sa.select(self.model_type)
                .where(*conditions)
                .order_by(self.model_type.end_license.desc())
                .offset(offset)
                .limit(page_size)
            )
            
            shops_result = await session.execute(shops_stmt)
            shops = shops_result.scalars().all()
            
            # Для каждого магазина получаем товары на продаже
            result = []
            for shop in shops:
                sale_items_stmt = (
                    sa.select(sale_items_subquery)
                    .where(sale_items_subquery.c.shop_id == shop.id)
                    .order_by(sale_items_subquery.c.sale_created_at.desc())
                )

                # ← НОВОЕ: в режиме поиска возвращаем только искомый товар
                if item_name:
                    sale_items_stmt = sale_items_stmt.where(
                        sale_items_subquery.c.item_name == item_name
                    )
                
                sale_items_result = await session.execute(sale_items_stmt)
                sale_items_rows = sale_items_result.all()
                
                sale_items = [
                    {
                        'sale_id': row.sale_id,
                        'inventory_item_id': row.inventory_item_id,
                        'price': row.price,
                        'item_slug': row.item_slug,
                        'amount': row.amount,
                        'expired_date': row.expired_date,
                        'used_count': row.used_count,
                        'wear': row.wear,
                        'item_name': row.item_name,
                        'ability_parameters': row.ability_parameters,
                        'parameters': row.parameters,           
                        'item_type': row.item_type,              
                        'minimal_level': row.minimal_level,     
                    }
                    for row in sale_items_rows
                ]
                
                shop_data = {
                    'id': shop.id,
                    'location_slug': shop.location_slug,
                    'character_id': shop.character_id,
                    'character_name': shop.character_name,
                    'name': shop.name,
                    'description': shop.description,
                    'level': shop.level,
                    'current_capacity': shop.current_capacity,
                    'photo_id': shop.photo_id,
                    'end_license': shop.end_license,
                    'number': shop.number,
                    'created_at': shop.created_at,
                    'updated_at': shop.updated_at,
                    'sale_items': sale_items
                }
                
                result.append(shop_data)
            
            return result, total_count

    async def recalculate_capacity(self: Self, shop_id: uuid.UUID) -> None:
        """Пересчитывает current_capacity из фактического веса предметов в лавке."""
        async with self.session as s:
            stmt = (
                sa.select(sa.func.coalesce(sa.func.sum(Item.weight * InventoryItem.amount), 0))
                .select_from(InventoryItem)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.shop_id == shop_id,
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > sa.func.now()
                    )
                )
            )
            total = (await s.scalar(stmt)) or 0

            await s.execute(
                sa.update(CityTradingShop)
                .where(CityTradingShop.id == shop_id)
                .values(current_capacity=int(total))
            )
            await s.commit()