import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session, joinedload

from .....core.utils.exceptions import ModelNotFoundException
from ...models import InventoryItem, Item
from ...schemas import (
    InventoryItemCreateSchema,
    InventoryItemReadSchema,
    InventoryItemSimpleReadSchema,
    ItemReadSchema,
)
from .character_items import _compute_expired_date


class CharacterItemSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_character_items(self, character_id: uuid.UUID, location_slug: str) -> list[InventoryItemReadSchema]:
        stmt = (
            sa.select(InventoryItem)
            .join(Item, InventoryItem.item_slug == Item.slug)
            .where(
                (InventoryItem.character_id == character_id) &
                (Item.location_slug == location_slug) &
                sa.or_(
                    InventoryItem.expired_date == None,
                    InventoryItem.expired_date > sa.func.now()
                )
            )
            .options(joinedload(InventoryItem.item))
            .order_by(InventoryItem.created_at.desc())
        )
        items = self.session.execute(stmt).scalars().unique().all()
        return [
            InventoryItemReadSchema(
                **{k: v for k, v in item.__dict__.items() if k != 'item' and not k.startswith('_')},
                item=ItemReadSchema.model_validate(item.item, from_attributes=True)
            )
            for item in items
        ]

    def get_items_from_location(self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemReadSchema]:
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
        items = self.session.execute(stmt).scalars().unique().all()
        return [
            InventoryItemReadSchema(
                **{k: v for k, v in item.__dict__.items() if k != 'item' and not k.startswith('_')},
                item=ItemReadSchema.model_validate(item.item, from_attributes=True)
            )
            for item in items
        ]

    def get_items_from_location_simple(self, character_id: uuid.UUID, location_slug: str, shop_id: uuid.UUID | None) -> list[InventoryItemSimpleReadSchema]:
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
                Item.name.label('item_name')
            )
            .join(Item, InventoryItem.item_slug == Item.slug)
            .where(sa.and_(*conditions))
            .order_by(InventoryItem.created_at.desc())
        )
        rows = self.session.execute(stmt).all()
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
                item_name=row.item_name
            )
            for row in rows
        ]

    def add_item(self, character_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        # Получаем информацию об item
        item_stmt = sa.select(Item).where(Item.slug == data.item_slug)
        item = self.session.execute(item_stmt).scalar_one()
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
            existing_item = self.session.execute(stmt_select).scalar_one_or_none()

            if existing_item:
                stmt_update = (
                    sa.update(InventoryItem)
                    .where(InventoryItem.id == existing_item.id)
                    .values(amount=InventoryItem.amount + data.amount)
                    .returning(InventoryItem.id)
                )
                self.session.execute(stmt_update)
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
                item_id = self.session.execute(stmt_insert).scalar_one()
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
                item_id = self.session.execute(stmt_insert).scalar_one()

        self.session.flush()

        # Загружаем полную запись
        stmt_final = (
            sa.select(InventoryItem)
            .options(joinedload(InventoryItem.item))
            .where(InventoryItem.id == item_id)
        )
        item_with_data = self.session.execute(stmt_final).scalar_one()
        item_dict = {k: v for k, v in item_with_data.__dict__.items() if k != 'item' and not k.startswith('_')}
        return InventoryItemReadSchema(
            **item_dict,
            item=ItemReadSchema.model_validate(item_with_data.item, from_attributes=True)
        )

    def add_item_to_shop(self, shop_id: uuid.UUID, data: InventoryItemCreateSchema) -> InventoryItemReadSchema:
        item_stmt = sa.select(Item).where(Item.slug == data.item_slug)
        item = self.session.execute(item_stmt).scalar_one()
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
            existing_item = self.session.execute(stmt_select).scalar_one_or_none()

            if existing_item:
                stmt_update = (
                    sa.update(InventoryItem)
                    .where(InventoryItem.id == existing_item.id)
                    .values(amount=InventoryItem.amount + data.amount)
                    .returning(InventoryItem.id)
                )
                self.session.execute(stmt_update)
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
                item_id = self.session.execute(stmt_insert).scalar_one()
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
                item_id = self.session.execute(stmt_insert).scalar_one()

        self.session.flush()

        stmt_final = (
            sa.select(InventoryItem)
            .options(joinedload(InventoryItem.item))
            .where(InventoryItem.id == item_id)
        )
        item_with_data = self.session.execute(stmt_final).scalar_one()
        item_dict = {k: v for k, v in item_with_data.__dict__.items() if k != 'item' and not k.startswith('_')}
        return InventoryItemReadSchema(
            **item_dict,
            item=ItemReadSchema.model_validate(item_with_data.item, from_attributes=True)
        )

    def get_by_id(self, item_id: uuid.UUID) -> InventoryItemReadSchema:
        stmt = (
            sa.select(InventoryItem)
            .options(joinedload(InventoryItem.item))
            .where(InventoryItem.id == item_id)
        )
        inventory_item = self.session.execute(stmt).scalar_one_or_none()
        if inventory_item is None:
            raise ModelNotFoundException(InventoryItem, item_id)
        item_dict = {k: v for k, v in inventory_item.__dict__.items() if k != 'item' and not k.startswith('_')}
        return InventoryItemReadSchema(
            **item_dict,
            item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True)
        )

    def get_by_id_and_character(self, item_id: uuid.UUID, character_id: uuid.UUID) -> InventoryItemReadSchema:
        stmt = (
            sa.select(InventoryItem)
            .options(joinedload(InventoryItem.item))
            .where(
                (InventoryItem.id == item_id) &
                (InventoryItem.character_id == character_id)
            )
        )
        inventory_item = self.session.execute(stmt).scalar_one_or_none()
        if inventory_item is None:
            raise ModelNotFoundException(InventoryItem, item_id)
        item_dict = {k: v for k, v in inventory_item.__dict__.items() if k != 'item' and not k.startswith('_')}
        return InventoryItemReadSchema(
            **item_dict,
            item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True)
        )

    def update_wear(self, item_id: uuid.UUID, character_id: uuid.UUID, wear: int) -> InventoryItemReadSchema:
        stmt = (
            sa.update(InventoryItem)
            .where(
                InventoryItem.id == item_id,
                InventoryItem.character_id == character_id,
            )
            .values(wear=wear)
            .returning(InventoryItem.id)
        )
        updated_id = self.session.execute(stmt).scalar_one_or_none()
        if updated_id is None:
            raise ModelNotFoundException(InventoryItem, item_id)
        self.session.flush()
        return self.get_by_id_and_character(item_id, character_id)

    def transfer_item_to_shop(self, item_id: uuid.UUID, shop_id: uuid.UUID) -> None:
        stmt = (
            sa.update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(character_id=None, shop_id=shop_id)
        )
        self.session.execute(stmt)

    def withdraw_item_from_shop(self, item_id: uuid.UUID, character_id: uuid.UUID) -> None:
        stmt = (
            sa.update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(shop_id=None, character_id=character_id)
        )
        self.session.execute(stmt)

    def transfer_item_to_buyer(self, item_id: uuid.UUID, buyer_character_id: uuid.UUID) -> None:
        stmt = (
            sa.update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(shop_id=None, character_id=buyer_character_id)
        )
        self.session.execute(stmt)

    def get_total_weight(self, character_id: uuid.UUID) -> int:
        """Суммарный вес всех предметов персонажа (weight * amount). Синхронный аналог async-версии."""
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
        result = self.session.scalar(stmt)
        return int(result or 0)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()