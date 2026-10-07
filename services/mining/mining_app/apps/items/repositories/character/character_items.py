import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol, Self

import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from ...enums import ItemType
from .....core.db import AsyncSession
from ...models import CharacterEquipment, InventoryItem, Item, SaleInventoryItem
from ...schemas import (
    InventoryItemCreateSchema,
    InventoryItemReadSchema,
    InventoryItemSimpleReadSchema,
    ItemReadSchema,
    InternalFurnitureItemSchema,
)


class CharacterItemRepositoryProtocol(Protocol):
    # ИЗМЕНЕНО: location_slug теперь опциональный (str | None)
    async def get_character_items(self: Self, character_id: uuid.UUID, location_slug: str | None = None) -> list[InventoryItemReadSchema]:
        ...
    
    async def get_items_from_location(self: Self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemReadSchema]:
        ...
    
    async def get_items_from_location_simple(self: Self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemSimpleReadSchema]:
        """Получает упрощенные items из локации (только с item_name вместо полного item)."""
        ...
    
    async def add_item(self: Self, character_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        ...

    async def add_item_to_shop(self: Self, shop_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        ...

    async def get_by_id(self: Self, item_id: uuid.UUID) -> InventoryItemReadSchema:
        """Получает InventoryItem по ID с подгрузкой Item."""
        ...

    async def get_by_id_and_character(self: Self, item_id: uuid.UUID, character_id: uuid.UUID) -> InventoryItemReadSchema:
        """Получает InventoryItem по ID и character_id с подгрузкой Item. Проверяет владельца."""
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

    async def update_wear(self: Self, item_id: uuid.UUID, character_id: uuid.UUID, wear: int) -> InventoryItemReadSchema:
        ...

    async def transfer_item_to_shop(
        self: Self,
        item_id: uuid.UUID,
        shop_id: uuid.UUID
    ) -> None:
        """Переносит конкретный InventoryItem в магазин (меняет character_id на NULL, shop_id на shop_id)."""
        ...

    async def withdraw_item_from_shop(
        self: Self,
        item_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> None:
        """Переносит конкретный InventoryItem из магазина персонажу (меняет shop_id на NULL, character_id на character_id)."""
        ...

    async def transfer_item_to_buyer(
        self: Self,
        item_id: uuid.UUID,
        buyer_character_id: uuid.UUID
    ) -> None:
        """Переносит InventoryItem покупателю (меняет shop_id на NULL, character_id на buyer_character_id)."""
        ...

    async def split_amount(self: Self, inventory_item_id: uuid.UUID, amount: int) -> uuid.UUID:
        """Отделяет amount шт. в новую строку InventoryItem, возвращает её id."""
        ...

    async def merge_identical_stack(self: Self, item_id: uuid.UUID) -> None:
        """Сливает строку с двойником той же партии (если двойник есть и не на продаже)."""
        ...

    async def consume_item(self: Self, inventory_item_id: uuid.UUID) -> None:
        """Использует предмет: уменьшает amount или удаляет если amount == 1."""
        ...

    async def get_total_weight(self: Self, character_id: uuid.UUID) -> int:
        """Суммарный вес всех предметов персонажа (weight * amount)."""
        ...

    async def get_character_furniture(
        self: Self,
        character_id: uuid.UUID
    ) -> list[InternalFurnitureItemSchema]:
        ...

    async def get_furniture_bulk(self: Self, inventory_item_ids: list[uuid.UUID]) -> list[InternalFurnitureItemSchema]: ...
    async def add_wear_bulk(self: Self, entries: list[tuple[uuid.UUID, int]]) -> list[uuid.UUID]: ...
    

def _compute_expired_date(item: "Item", existing_date) -> datetime | None:
    """Вычисляет срок годности из min/max_shelf_life_days справочника,
    если expired_date не был передан явно."""
    if existing_date is not None:
        return existing_date
    if item.min_shelf_life_days is None or item.max_shelf_life_days is None:
        return None
    days = random.randint(item.min_shelf_life_days, item.max_shelf_life_days)
    seconds = random.randint(0, 86400 - 1)
    return datetime.now(UTC) + timedelta(days=days, seconds=seconds)


class CharacterItemRepository(CharacterItemRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session
    
    # ИЗМЕНЕНО: location_slug опциональный, фильтр применяется только если передан
    async def get_character_items(self: Self, character_id: uuid.UUID, location_slug: str | None = None) -> list[InventoryItemReadSchema]:
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.character_id == character_id,
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > sa.func.now()
                    )
                )
            )
            
            # Фильтр по локации ТОЛЬКО если location_slug передан
            if location_slug:
                stmt = stmt.where(Item.location_slug == location_slug)
            
            stmt = stmt.options(joinedload(InventoryItem.item)).order_by(InventoryItem.created_at.desc())
            
            result = await s.scalars(stmt)
            items = result.unique().all()
            
            return [
                InventoryItemReadSchema(
                    **{k: v for k, v in item.__dict__.items() if k != 'item' and not k.startswith('_')},
                    item=ItemReadSchema.model_validate(item.item, from_attributes=True)
                )
                for item in items
            ]
    
    async def get_items_from_location(self: Self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemReadSchema]:
        async with self.session as s:
            conditions = [
                Item.location_slug == location_slug,
                sa.or_(
                    InventoryItem.expired_date == None,
                    InventoryItem.expired_date > sa.func.now()
                )
            ]
            
            if shop_id:
                conditions.append(
                    sa.or_(
                        InventoryItem.character_id == character_id,
                        InventoryItem.shop_id == shop_id
                    )
                )
            else:
                conditions.append(InventoryItem.character_id == character_id)
            
            stmt = (
                sa.select(InventoryItem)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(sa.and_(*conditions))
                .options(joinedload(InventoryItem.item))
                .order_by(InventoryItem.created_at.desc())
            )
            
            result = await s.scalars(stmt)
            items = result.unique().all()
            
            return [
                InventoryItemReadSchema(
                    **{k: v for k, v in item.__dict__.items() if k != 'item' and not k.startswith('_')},
                    item=ItemReadSchema.model_validate(item.item, from_attributes=True)
                )
                for item in items
            ]
    
    async def get_items_from_location_simple(self: Self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemSimpleReadSchema]:
        """Получает упрощённые items из локации (только с item_name вместо полного item)."""
        async with self.session as s:
            # Маппинг: trade-hall видит предметы из forge и jewelers
            TRADE_HALL_SLUG = "1.27.trade-hall"
            EQUIPMENT_LOCATIONS = {"1.13.forge", "1.16.jewelers"}
            
            if location_slug == TRADE_HALL_SLUG:
                conditions = [
                    Item.location_slug.in_(EQUIPMENT_LOCATIONS),
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > sa.func.now()
                    )
                ]
            else:
                conditions = [
                    Item.location_slug == location_slug,
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > sa.func.now()
                    )
                ]

            if shop_id:
                conditions.append(
                    sa.or_(
                        InventoryItem.character_id == character_id,
                        InventoryItem.shop_id == shop_id
                    )
                )
            else:
                conditions.append(InventoryItem.character_id == character_id)
                       
            conditions.append(
                InventoryItem.id.not_in(
                    sa.select(CharacterEquipment.inventory_item_id)
                )
            )

            stmt = (
                sa.select(
                    InventoryItem.id,
                    InventoryItem.character_id,
                    InventoryItem.shop_id,
                    InventoryItem.deal_id,
                    InventoryItem.item_slug,
                    InventoryItem.amount,
                    InventoryItem.expired_date,
                    InventoryItem.used_count,
                    InventoryItem.wear,
                    InventoryItem.created_at,
                    InventoryItem.updated_at,
                    Item.name.label('item_name'),
                    Item.parameters,
                    Item.item_type,
                    Item.minimal_level,
                    Item.ability_parameters,
                    Item.price.label('price'), 
                    Item.weight,     
                )
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(sa.and_(*conditions))
                .order_by(InventoryItem.created_at.desc())
            )

            result = await s.execute(stmt)
            rows = result.all()

            return [
                InventoryItemSimpleReadSchema(
                    id=row.id,
                    character_id=row.character_id,
                    shop_id=row.shop_id,
                    deal_id=row.deal_id,
                    item_slug=row.item_slug,
                    amount=row.amount,
                    expired_date=row.expired_date,
                    used_count=row.used_count,
                    wear=row.wear,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    item_name=row.item_name,
                    parameters=row.parameters,
                    item_type=row.item_type,
                    minimal_level=row.minimal_level,
                    ability_parameters=row.ability_parameters,
                    price=row.price,
                    weight=row.weight,
                )
                for row in rows
            ]
    
    async def add_item(self: Self, character_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        async with self.session as s:
            stmt_item = sa.select(Item).where(Item.slug == data.item_slug)
            result_item = await s.execute(stmt_item)
            item = result_item.scalar_one()                        
            expired_date = _compute_expired_date(item, data.expired_date)
            
            if item.is_stackable:
                # Стакающиеся предметы — ищем существующий и сливаем
                stmt_select = (
                    sa.select(InventoryItem)
                    .where(
                        (InventoryItem.character_id == character_id) &
                        (InventoryItem.shop_id.is_(None)) &
                        (InventoryItem.item_slug == data.item_slug) &
                        (InventoryItem.expired_date == expired_date) &
                        (InventoryItem.used_count == data.used_count) &
                        (InventoryItem.wear == data.wear) &
                        (InventoryItem.item_binding_type == data.item_binding_type)
                    )
                )
                result = await s.execute(stmt_select)
                existing_item = result.scalar_one_or_none()
                
                if existing_item:
                    stmt_update = (
                        sa.update(InventoryItem)
                        .where(InventoryItem.id == existing_item.id)
                        .values(amount=InventoryItem.amount + data.amount)
                        .returning(InventoryItem.id)
                    )
                    await s.execute(stmt_update)
                    item_id = existing_item.id
                else:
                    stmt_insert = (
                        sa.insert(InventoryItem)
                        .values(
                            character_id=character_id,
                            shop_id=None,
                            item_slug=data.item_slug,
                            amount=data.amount,
                            expired_date=expired_date,
                            used_count=data.used_count,
                            wear=data.wear,
                            item_binding_type=data.item_binding_type,
                        )
                        .returning(InventoryItem.id)
                    )
                    result_insert = await s.execute(stmt_insert)
                    item_id = result_insert.scalar_one()
            else:
                # Нестакающиеся предметы — отдельная строка на каждую штуку
                stmt_insert = (
                    sa.insert(InventoryItem)
                    .values(
                        character_id=character_id,
                        shop_id=None,
                        item_slug=data.item_slug,
                        amount=1,
                        expired_date=expired_date,
                        used_count=data.used_count,
                        wear=data.wear,
                        item_binding_type=data.item_binding_type,
                    )
                    .returning(InventoryItem.id)
                )
                item_id = None
                for _ in range(data.amount):
                    result_insert = await s.execute(stmt_insert)
                    item_id = result_insert.scalar_one()
            
            await s.commit()
            
            stmt_final = (
                sa.select(InventoryItem)
                .options(joinedload(InventoryItem.item))
                .where(InventoryItem.id == item_id)
            )
            result_final = await s.execute(stmt_final)
            item_with_data = result_final.scalar_one()
            
            item_dict = {k: v for k, v in item_with_data.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return InventoryItemReadSchema(
                **item_dict,
                item=ItemReadSchema.model_validate(item_with_data.item, from_attributes=True)
            )

    async def add_item_to_shop(self: Self, shop_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        async with self.session as s:
            stmt_item = sa.select(Item).where(Item.slug == data.item_slug)
            result_item = await s.execute(stmt_item)
            item = result_item.scalar_one()            
            expired_date = _compute_expired_date(item, data.expired_date)

            if item.is_stackable:
                # Стакающиеся предметы — ищем существующий и сливаем
                stmt_select = (
                    sa.select(InventoryItem)
                    .where(
                        (InventoryItem.character_id.is_(None)) &
                        (InventoryItem.shop_id == shop_id) &
                        (InventoryItem.item_slug == data.item_slug) &
                        (InventoryItem.expired_date == expired_date) &
                        (InventoryItem.used_count == data.used_count) &
                        (InventoryItem.wear == data.wear) &
                        (InventoryItem.item_binding_type == data.item_binding_type)
                    )
                )
                result = await s.execute(stmt_select)
                existing_item = result.scalar_one_or_none()

                if existing_item:
                    stmt_update = (
                        sa.update(InventoryItem)
                        .where(InventoryItem.id == existing_item.id)
                        .values(amount=InventoryItem.amount + data.amount)
                        .returning(InventoryItem.id)
                    )
                    await s.execute(stmt_update)
                    item_id = existing_item.id
                else:
                    stmt_insert = (
                        sa.insert(InventoryItem)
                        .values(
                            character_id=None,
                            shop_id=shop_id,
                            item_slug=data.item_slug,
                            amount=data.amount,
                            expired_date=expired_date,
                            used_count=data.used_count,
                            wear=data.wear,
                            item_binding_type=data.item_binding_type,
                        )
                        .returning(InventoryItem.id)
                    )
                    result_insert = await s.execute(stmt_insert)
                    item_id = result_insert.scalar_one()
            else:
                # Нестакающиеся предметы — отдельная строка на каждую штуку
                stmt_insert = (
                    sa.insert(InventoryItem)
                    .values(
                        character_id=None,
                        shop_id=shop_id,
                        item_slug=data.item_slug,
                        amount=1,
                        expired_date=expired_date,
                        used_count=data.used_count,
                        wear=data.wear,
                        item_binding_type=data.item_binding_type,
                    )
                    .returning(InventoryItem.id)
                )
                item_id = None
                for _ in range(data.amount):
                    result_insert = await s.execute(stmt_insert)
                    item_id = result_insert.scalar_one()

            await s.commit()

            stmt_final = (
                sa.select(InventoryItem)
                .options(joinedload(InventoryItem.item))
                .where(InventoryItem.id == item_id)
            )
            result_final = await s.execute(stmt_final)
            item_with_data = result_final.scalar_one()
            item_dict = {k: v for k, v in item_with_data.__dict__.items() if k != 'item' and not k.startswith('_')}

            return InventoryItemReadSchema(
                **item_dict,
                item=ItemReadSchema.model_validate(item_with_data.item, from_attributes=True)
            )

    async def get_by_id(self: Self, item_id: uuid.UUID) -> InventoryItemReadSchema:
        """Получает InventoryItem по ID с подгрузкой Item."""
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .options(joinedload(InventoryItem.item))
                .where(InventoryItem.id == item_id)
            )
            
            result = await s.execute(stmt)
            inventory_item = result.scalar_one_or_none()
            
            if inventory_item is None:
                from .....core.utils.exceptions import ModelNotFoundException
                raise ModelNotFoundException(InventoryItem, item_id)
            
            item_dict = {k: v for k, v in inventory_item.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return InventoryItemReadSchema(
                **item_dict,
                item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True)
            )

    async def get_by_id_and_character(self: Self, item_id: uuid.UUID, character_id: uuid.UUID) -> InventoryItemReadSchema:
        """Получает InventoryItem по ID и character_id с подгрузкой Item. Проверяет владельца."""
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .options(joinedload(InventoryItem.item))
                .where(
                    (InventoryItem.id == item_id) &
                    (InventoryItem.character_id == character_id)
                )
            )
            
            result = await s.execute(stmt)
            inventory_item = result.scalar_one_or_none()
            
            if inventory_item is None:
                from .....core.utils.exceptions import ModelNotFoundException
                raise ModelNotFoundException(InventoryItem, item_id)
            
            item_dict = {k: v for k, v in inventory_item.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return InventoryItemReadSchema(
                **item_dict,
                item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True)
            )

    async def take_item(
        self: Self,
        character_id: uuid.UUID,
        amount: int,
        inventory_item_id: uuid.UUID | None = None,
        item_slug: str | None = None,
        force: bool = False,
    ) -> None:
        from .....core.utils.exceptions import ModelNotFoundException, ValidationError

        async with self.session as session, session.begin():
            conditions = [InventoryItem.character_id == character_id]
            if inventory_item_id is not None:
                conditions.append(InventoryItem.id == inventory_item_id)
            else:
                conditions.append(InventoryItem.item_slug == item_slug)

            statement = (
                sa.select(InventoryItem)
                .where(*conditions)
                .order_by(InventoryItem.created_at.asc())
                .with_for_update()
            )
            items = list((await session.execute(statement)).scalars().all())
            if not items:
                if inventory_item_id is not None:
                    raise ModelNotFoundException(InventoryItem, inventory_item_id)
                raise ValidationError(field="item_slug", message="Character does not own this item")

            remaining = amount
            selected: list[tuple[InventoryItem, int]] = []
            for item in items:
                taken = min(item.amount, remaining)
                selected.append((item, taken))
                remaining -= taken
                if remaining == 0:
                    break

            if remaining:
                raise ValidationError(field="amount", message="Character does not own enough items")

            selected_ids = [item.id for item, _ in selected]
            equipment_statement = sa.select(CharacterEquipment.inventory_item_id).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.inventory_item_id.in_(selected_ids),
            )
            equipped_ids = set((await session.execute(equipment_statement)).scalars().all())
            if equipped_ids and not force:
                raise ValidationError(field="force", message="Cannot take equipped items without force=true")

            if equipped_ids:
                await session.execute(
                    sa.delete(CharacterEquipment).where(
                        CharacterEquipment.character_id == character_id,
                        CharacterEquipment.inventory_item_id.in_(equipped_ids),
                    )
                )

            for item, taken in selected:
                if item.amount == taken:
                    await session.delete(item)
                else:
                    item.amount -= taken

    async def update_wear(self: Self, item_id: uuid.UUID, character_id: uuid.UUID, wear: int) -> InventoryItemReadSchema:
        async with self.session as session, session.begin():
            statement = (
                sa.update(InventoryItem)
                .where(
                    InventoryItem.id == item_id,
                    InventoryItem.character_id == character_id,
                )
                .values(wear=wear)
                .returning(InventoryItem.id)
            )
            updated_id = (await session.execute(statement)).scalar_one_or_none()
            if updated_id is None:
                from .....core.utils.exceptions import ModelNotFoundException
                raise ModelNotFoundException(InventoryItem, item_id)
        return await self.get_by_id_and_character(item_id, character_id)

    async def transfer_item_to_shop(
        self: Self,
        item_id: uuid.UUID,
        shop_id: uuid.UUID
    ) -> None:
        """Переносит конкретный InventoryItem в магазин."""
        async with self.session as s:
            stmt_update = (
                sa.update(InventoryItem)
                .where(InventoryItem.id == item_id)
                .values(
                    character_id=None,
                    shop_id=shop_id
                )
            )
            
            await s.execute(stmt_update)
            await s.commit()

    async def withdraw_item_from_shop(
        self: Self,
        item_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> None:
        """Переносит конкретный InventoryItem из магазина персонажу."""
        async with self.session as s:
            stmt_update = (
                sa.update(InventoryItem)
                .where(InventoryItem.id == item_id)
                .values(
                    shop_id=None,
                    character_id=character_id
                )
            )
            
            await s.execute(stmt_update)
            await s.commit()

    async def transfer_item_to_buyer(
        self: Self,
        item_id: uuid.UUID,
        buyer_character_id: uuid.UUID
    ) -> None:
        """Переносит InventoryItem покупателю (меняет shop_id на NULL, character_id на buyer_character_id)."""
        async with self.session as s:
            stmt_update = (
                sa.update(InventoryItem)
                .where(InventoryItem.id == item_id)
                .values(
                    shop_id=None,
                    character_id=buyer_character_id
                )
            )
            
            await s.execute(stmt_update)
            await s.commit()

    async def split_amount(self: Self, inventory_item_id: uuid.UUID, amount: int) -> uuid.UUID:
        """Отделяет amount шт. в новую строку InventoryItem, возвращает её id."""
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .where(InventoryItem.id == inventory_item_id)
                .with_for_update()
            )
            original = (await s.execute(stmt)).scalar_one_or_none()
            if original is None or amount < 1 or amount >= original.amount:
                from .....core.utils.exceptions import ValidationError
                raise ValidationError(field="amount", message="Invalid split amount")

            new_row = InventoryItem(
                character_id=original.character_id,
                shop_id=original.shop_id,
                item_slug=original.item_slug,
                amount=amount,
                expired_date=original.expired_date,
                used_count=original.used_count,
                wear=original.wear,
                item_binding_type=original.item_binding_type,
            )
            s.add(new_row)
            await s.flush()
            new_id = new_row.id
            original.amount = original.amount - amount
            await s.commit()
            return new_id

    async def merge_identical_stack(self: Self, item_id: uuid.UUID) -> None:
        """Если у строки есть двойник(и) с теми же полями партии (и все не на продаже) —
        сливает их все в одну строку. Разные крафты не сливаются: у них разный expired_date."""
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .where(InventoryItem.id == item_id)
                .with_for_update()
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            if row is None:
                return

            # Страховка: не стакаем нестакающиеся предметы
            stackable = (await s.execute(
                sa.select(Item.is_stackable).where(Item.slug == row.item_slug)
            )).scalar_one_or_none()
            if not stackable:
                return

            on_sale_count = (await s.execute(
                sa.select(sa.func.count())
                .select_from(SaleInventoryItem)
                .where(SaleInventoryItem.inventory_item_id == row.id)
            )).scalar_one()
            if on_sale_count > 0:
                await s.commit()
                return

            if row.character_id is not None:
                owner_cond = (
                    (InventoryItem.character_id == row.character_id) &
                    (InventoryItem.shop_id.is_(None))
                )
            else:
                owner_cond = (
                    (InventoryItem.character_id.is_(None)) &
                    (InventoryItem.shop_id == row.shop_id)
                )

            on_sale_subq = (
                sa.select(SaleInventoryItem.inventory_item_id)
                .scalar_subquery()
            )

            while True:
                twin_stmt = (
                    sa.select(InventoryItem)
                    .where(
                        InventoryItem.id != row.id,
                        owner_cond,
                        InventoryItem.item_slug == row.item_slug,
                        InventoryItem.expired_date == row.expired_date,
                        InventoryItem.used_count == row.used_count,
                        InventoryItem.wear == row.wear,
                        InventoryItem.item_binding_type == row.item_binding_type,
                        InventoryItem.id.not_in(on_sale_subq),
                    )
                    .with_for_update()
                )
                twin = (await s.execute(twin_stmt)).scalars().first()
                if twin is None:
                    break

                row.amount = row.amount + twin.amount
                await s.execute(
                    sa.delete(InventoryItem).where(InventoryItem.id == twin.id)
                )

            await s.commit()

    async def consume_item(self: Self, inventory_item_id: uuid.UUID) -> None:
        """Использует предмет: уменьшает amount или удаляет если amount == 1."""
        async with self.session as s:
            stmt = (
                sa.select(InventoryItem)
                .where(InventoryItem.id == inventory_item_id)
                .with_for_update()
            )
            result = await s.execute(stmt)
            inventory_item = result.scalar_one_or_none()

            if inventory_item is None:
                from .....core.utils.exceptions import ModelNotFoundException
                raise ModelNotFoundException(InventoryItem, inventory_item_id)

            if inventory_item.amount > 1:
                inventory_item.amount -= 1
            else:
                await s.delete(inventory_item)

            await s.commit()

    async def get_total_weight(self: Self, character_id: uuid.UUID) -> int:
        async with self.session as s:
            stmt = (
                sa.select(sa.func.coalesce(sa.func.sum(Item.weight * InventoryItem.amount), 0))
                .select_from(InventoryItem)
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.character_id == character_id,
                    sa.or_(
                        InventoryItem.expired_date == None,
                        InventoryItem.expired_date > sa.func.now()
                    )
                )
            )
            result = await s.scalar(stmt)
            return int(result or 0)

    async def get_character_furniture(
        self: Self,
        character_id: uuid.UUID
    ) -> list[InternalFurnitureItemSchema]:
        async with self.session as s:
            stmt = (
                sa.select(
                    InventoryItem.id.label("inventory_item_id"),
                    InventoryItem.item_slug.label("slug"),
                    InventoryItem.wear.label("wear"),
                    InventoryItem.shop_id.label("shop_id"),
                    Item.parameters.label("parameters"),
                    Item.weight.label("weight"),
                    Item.ability_parameters.label("ability_parameters"),
                    Item.name.label("name"),
                )
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.character_id == character_id,
                    InventoryItem.deal_id.is_(None),
                    Item.item_type == ItemType.FURNITURE,
                )
                .order_by(InventoryItem.created_at.desc())
            )

            result = await s.execute(stmt)
            rows = result.all()

            return [
                InternalFurnitureItemSchema(
                    inventory_item_id=row.inventory_item_id,
                    slug=row.slug,
                    wear=row.wear or 0,
                    shop_id=row.shop_id,
                    max_wear=(row.parameters or {}).get("max_wear"),
                    volume=(row.parameters or {}).get("volume"),
                    weight=row.weight,
                    ability_parameters=row.ability_parameters,
                    name=row.name,
                )
                for row in rows
            ]


    async def get_furniture_bulk(self: Self, inventory_item_ids: list[uuid.UUID]) -> list[InternalFurnitureItemSchema]:
        """Чтение мебели пачкой по списку inventory_item_id (без привязки к персонажу)."""
        if not inventory_item_ids:
            return []
        async with self.session as s:
            stmt = (
                sa.select(
                    InventoryItem.id.label("inventory_item_id"),
                    InventoryItem.item_slug.label("slug"),
                    InventoryItem.wear.label("wear"),
                    Item.parameters.label("parameters"),
                    Item.weight.label("weight"),
                    Item.ability_parameters.label("ability_parameters"),
                    Item.name.label("name"),
                )
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(
                    InventoryItem.id.in_(inventory_item_ids),
                    Item.item_type == ItemType.FURNITURE,
                )
            )
            result = await s.execute(stmt)
            rows = result.all()
            return [
                InternalFurnitureItemSchema(
                    inventory_item_id=row.inventory_item_id,
                    slug=row.slug,
                    wear=row.wear or 0,
                    max_wear=(row.parameters or {}).get("max_wear"),
                    volume=(row.parameters or {}).get("volume"),
                    weight=row.weight,
                    ability_parameters=row.ability_parameters,
                    name=row.name,
                )
                for row in rows
            ]

    async def add_wear_bulk(self: Self, entries: list[tuple[uuid.UUID, int]]) -> list[uuid.UUID]:
        """
        Инкремент wear с капом по max_wear, одной транзакцией.
        Уже сломанные (wear >= max_wear) не трогаем.
        Возвращает id, которые достигли max_wear ИМЕННО этим вызовом.
        """
        if not entries:
            return []
        add_by_id = dict(entries)
        broken: list[uuid.UUID] = []
        async with self.session as session, session.begin():
            stmt = (
                sa.select(
                    InventoryItem.id,
                    InventoryItem.wear,
                    sa.cast(Item.parameters.op('->>')('max_wear'), sa.Integer).label('max_wear'),
                )
                .join(Item, InventoryItem.item_slug == Item.slug)
                .where(InventoryItem.id.in_(list(add_by_id.keys())))
            )
            rows = (await session.execute(stmt)).all()
            for row in rows:
                if row.max_wear is None:
                    continue
                old_wear = row.wear or 0
                if old_wear >= row.max_wear:
                    continue
                new_wear = min(old_wear + add_by_id[row.id], row.max_wear)
                await session.execute(
                    sa.update(InventoryItem)
                    .where(InventoryItem.id == row.id)
                    .values(wear=new_wear)
                )
                if new_wear >= row.max_wear:
                    broken.append(row.id)
        return broken
