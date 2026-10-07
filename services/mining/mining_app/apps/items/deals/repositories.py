import uuid
from datetime import datetime
from typing import Protocol

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ...resources.models import CharacterResource, Resource
from ..models import CharacterEquipment, InventoryItem, Item, SaleInventoryItem
from .enums import DealAssetType, DealStatus, ResourceReservationStatus
from .models import (
    Deal,
    DealItem,
    DealLedgerOperation,
    DealOffer,
    DealResourceReservation,
    TradeLicense,
)


class DealRepositoryProtocol(Protocol):
    session: AsyncSession

    async def get_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> Deal | None: ...
    async def get_detail_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID) -> tuple[Deal, list[DealOffer], list[DealItem]] | None: ...
    async def list_for_participant(self, character_id: uuid.UUID, statuses: list[DealStatus] | None, limit: int, offset: int) -> tuple[list[Deal], int]: ...
    async def get_for_update(self, deal_id: uuid.UUID) -> Deal | None: ...
    async def list_expired_for_update(self, now: datetime, limit: int) -> list[Deal]: ...
    async def list_completing_for_update(self, limit: int) -> list[Deal]: ...
    async def list_completing(self, limit: int) -> list[Deal]: ...
    async def list_active_for_character(self, character_id: uuid.UUID) -> list["Deal"]: ...
    

class DealOfferRepositoryProtocol(Protocol):
    session: AsyncSession

    async def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealOffer]: ...
    async def get_for_character(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> DealOffer | None: ...


class DealItemRepositoryProtocol(Protocol):
    session: AsyncSession

    async def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealItem]: ...
    async def clear_inventory_deal_id(self, deal_id: uuid.UUID) -> None: ...
    async def get_for_offer_asset(self, offer_id: uuid.UUID, asset_type: DealAssetType, resource_slug: str | None = None, for_update: bool = False) -> DealItem | None: ...
    async def get_for_deal_item(self, deal_id: uuid.UUID, deal_item_id: uuid.UUID, for_update: bool = False) -> DealItem | None: ...
    async def get_inventory_for_trade(self, inventory_item_id: uuid.UUID, for_update: bool = False) -> tuple[InventoryItem, Item, bool, bool] | None: ...
    async def incoming_weight(self, deal_id: uuid.UUID, recipient_id: uuid.UUID) -> int: ...
    async def transfer_assets(self, deal: Deal, items: list[DealItem]) -> None: ...


class DealResourceReservationRepositoryProtocol(Protocol):
    session: AsyncSession

    async def release_active_for_deal(self, deal_id: uuid.UUID) -> None: ...
    async def get_active_for_item(self, deal_item_id: uuid.UUID, for_update: bool = False) -> DealResourceReservation | None: ...
    async def reserved_amount(self, character_id: uuid.UUID, resource_slug: str) -> int: ...
    async def mark_transferred_for_deal(self, deal_id: uuid.UUID) -> None: ...


class DealLedgerOperationRepositoryProtocol(Protocol):
    session: AsyncSession

    async def create_many(self, operations: list[DealLedgerOperation]) -> None: ...
    async def get_by_operation_id(self, operation_id: uuid.UUID) -> DealLedgerOperation | None: ...


class TradeLicenseRepositoryProtocol(Protocol):
    session: AsyncSession


class DealRepository:
    model_type = Deal

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> Deal | None:
        statement = sa.select(Deal).where(
            Deal.id == deal_id,
            sa.or_(Deal.initiator_character_id == character_id, Deal.partner_character_id == character_id),
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_for_update(self, deal_id: uuid.UUID) -> Deal | None:
        return await self.session.scalar(sa.select(Deal).where(Deal.id == deal_id).with_for_update())

    async def list_expired_for_update(self, now: datetime, limit: int) -> list[Deal]:
        statement = (
            sa.select(Deal)
            .where(Deal.status.in_((DealStatus.DRAFT, DealStatus.ACTIVE)), Deal.expires_at <= now)
            .order_by(Deal.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list((await self.session.scalars(statement)).all())

    async def list_completing_for_update(self, limit: int) -> list[Deal]:
        statement = (
            sa.select(Deal).where(Deal.status == DealStatus.COMPLETING)
            .order_by(Deal.updated_at).limit(limit).with_for_update(skip_locked=True)
        )
        return list((await self.session.scalars(statement)).all())

    async def list_completing(self, limit: int) -> list[Deal]:
        statement = sa.select(Deal).where(Deal.status == DealStatus.COMPLETING).order_by(Deal.updated_at).limit(limit)
        return list((await self.session.scalars(statement)).all())

    async def get_detail_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID) -> tuple[Deal, list[DealOffer], list[DealItem]] | None:
        statement = (
            sa.select(Deal, DealOffer, DealItem)
            .outerjoin(DealOffer, DealOffer.deal_id == Deal.id)
            .outerjoin(DealItem, DealItem.deal_id == Deal.id)
            .where(
                Deal.id == deal_id,
                sa.or_(Deal.initiator_character_id == character_id, Deal.partner_character_id == character_id),
            )
        )
        rows = (await self.session.execute(statement)).all()
        if not rows:
            return None
        deal = rows[0].Deal
        offers = {offer.id: offer for _, offer, _ in rows if offer is not None}
        items = {item.id: item for _, _, item in rows if item is not None}
        return deal, list(offers.values()), list(items.values())

    async def list_for_participant(self, character_id: uuid.UUID, statuses: list[DealStatus] | None, limit: int, offset: int) -> tuple[list[Deal], int]:
        conditions = [sa.or_(Deal.initiator_character_id == character_id, Deal.partner_character_id == character_id)]
        if statuses:
            conditions.append(Deal.status.in_(statuses))
        statement = sa.select(Deal).where(*conditions).order_by(Deal.updated_at.desc())
        count = await self.session.scalar(sa.select(sa.func.count()).select_from(statement.subquery()))
        deals = (await self.session.scalars(statement.limit(limit).offset(offset))).all()
        return deals, count or 0

    async def list_active_for_character(self, character_id: uuid.UUID) -> list[Deal]:
        """Возвращает все сделки в статусах DRAFT или ACTIVE, где участвует персонаж."""
        result = await self.session.execute(
            sa.select(Deal).where(
                sa.or_(
                    Deal.initiator_character_id == character_id,
                    Deal.partner_character_id == character_id
                ),
                Deal.status.in_([DealStatus.DRAFT, DealStatus.ACTIVE])
            )
        )
        return list(result.scalars().all())


class DealOfferRepository:
    model_type = DealOffer

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealOffer]:
        statement = sa.select(DealOffer).where(DealOffer.deal_id == deal_id).order_by(DealOffer.created_at)
        if for_update:
            statement = statement.with_for_update()
        return (await self.session.scalars(statement)).all()

    async def get_for_character(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> DealOffer | None:
        statement = sa.select(DealOffer).where(DealOffer.deal_id == deal_id, DealOffer.character_id == character_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)


class DealItemRepository:
    model_type = DealItem

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealItem]:
        statement = sa.select(DealItem).where(DealItem.deal_id == deal_id).order_by(DealItem.created_at)
        if for_update:
            statement = statement.with_for_update()
        return list((await self.session.scalars(statement)).all())

    async def clear_inventory_deal_id(self, deal_id: uuid.UUID) -> None:
        await self.session.execute(sa.update(InventoryItem).where(InventoryItem.deal_id == deal_id).values(deal_id=None))

    async def get_for_offer_asset(self, offer_id: uuid.UUID, asset_type: DealAssetType, resource_slug: str | None = None, for_update: bool = False) -> DealItem | None:
        statement = sa.select(DealItem).where(DealItem.offer_id == offer_id, DealItem.asset_type == asset_type)
        if resource_slug is not None:
            statement = statement.where(DealItem.resource_slug == resource_slug)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_for_deal_item(self, deal_id: uuid.UUID, deal_item_id: uuid.UUID, for_update: bool = False) -> DealItem | None:
        statement = sa.select(DealItem).where(DealItem.id == deal_item_id, DealItem.deal_id == deal_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_inventory_for_trade(
        self, inventory_item_id: uuid.UUID, for_update: bool = False
    ) -> tuple[InventoryItem, Item, bool, bool] | None:
        """
        Получает inventory_item с item и флагами equipped/for_sale для проверки возможности добавления в сделку.
        
        Returns:
            tuple[InventoryItem, Item, equipped, for_sale] или None если не найдено
        """
        # Подзапрос с FOR UPDATE только на inventory_items (без outer join)
        inventory_stmt = sa.select(InventoryItem).where(
            InventoryItem.id == inventory_item_id
        )
        if for_update:
            inventory_stmt = inventory_stmt.with_for_update()
        
        inventory_item = (await self.session.execute(inventory_stmt)).scalar_one_or_none()
        if not inventory_item:
            return None
        
        # Теперь загружаем item без FOR UPDATE
        item = (await self.session.execute(
            sa.select(Item).where(Item.slug == inventory_item.item_slug)
        )).scalar_one()
        
        # Проверяем equipped
        equipped = (await self.session.execute(
            sa.select(CharacterEquipment.id).where(
                CharacterEquipment.inventory_item_id == inventory_item_id
            )
        )).scalar_one_or_none() is not None
        
        # Проверяем for_sale
        for_sale = (await self.session.execute(
            sa.select(SaleInventoryItem.id).where(
                SaleInventoryItem.inventory_item_id == inventory_item_id
            )
        )).scalar_one_or_none() is not None
        
        return inventory_item, item, equipped, for_sale

    async def incoming_weight(self, deal_id: uuid.UUID, recipient_id: uuid.UUID) -> int:
        owner_id = sa.case(
            (Deal.initiator_character_id == recipient_id, Deal.partner_character_id),
            else_=Deal.initiator_character_id,
        )
        inventory_weight = sa.select(sa.func.coalesce(sa.func.sum(DealItem.amount * Item.weight), 0)).join(InventoryItem, InventoryItem.id == DealItem.inventory_item_id).join(Item, Item.slug == InventoryItem.item_slug).join(Deal, Deal.id == DealItem.deal_id).where(DealItem.deal_id == deal_id, DealItem.asset_type == DealAssetType.INVENTORY_ITEM, DealItem.owner_character_id == owner_id)
        resource_weight = sa.select(sa.func.coalesce(sa.func.sum(DealItem.amount * Resource.weight), 0)).join(Resource, Resource.slug == DealItem.resource_slug).join(Deal, Deal.id == DealItem.deal_id).where(DealItem.deal_id == deal_id, DealItem.asset_type == DealAssetType.RESOURCE, DealItem.owner_character_id == owner_id)
        return int((await self.session.scalar(inventory_weight)) or 0) + int((await self.session.scalar(resource_weight)) or 0)

    async def transfer_assets(self, deal: Deal, items: list[DealItem]) -> None:
        for item in items:
            recipient_id = deal.partner_character_id if item.owner_character_id == deal.initiator_character_id else deal.initiator_character_id
            if item.asset_type == DealAssetType.INVENTORY_ITEM:
                inventory_item = await self.session.get(InventoryItem, item.inventory_item_id, with_for_update=True)
                if inventory_item is None or inventory_item.deal_id != deal.id:
                    raise ValueError("Deal inventory item is no longer locked")
                inventory_item.character_id = recipient_id
                inventory_item.deal_id = None
                continue
            source = await self.session.scalar(sa.select(CharacterResource).where(CharacterResource.character_id == item.owner_character_id, CharacterResource.resource_slug == item.resource_slug).with_for_update())
            if source is None or source.amount < item.amount:
                raise ValueError("Reserved resource is no longer available")
            target = await self.session.scalar(sa.select(CharacterResource).where(CharacterResource.character_id == recipient_id, CharacterResource.resource_slug == item.resource_slug).with_for_update())
            source.amount -= item.amount
            if target is None:
                self.session.add(CharacterResource(character_id=recipient_id, resource_slug=item.resource_slug, amount=item.amount))
            else:
                target.amount += item.amount


class DealResourceReservationRepository:
    model_type = DealResourceReservation

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def release_active_for_deal(self, deal_id: uuid.UUID) -> None:
        await self.session.execute(
            sa.update(DealResourceReservation)
            .where(DealResourceReservation.deal_id == deal_id, DealResourceReservation.status == ResourceReservationStatus.ACTIVE)
            .values(status=ResourceReservationStatus.RELEASED)
        )

    async def get_active_for_item(self, deal_item_id: uuid.UUID, for_update: bool = False) -> DealResourceReservation | None:
        statement = sa.select(DealResourceReservation).where(DealResourceReservation.deal_item_id == deal_item_id, DealResourceReservation.status == ResourceReservationStatus.ACTIVE)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def reserved_amount(self, character_id: uuid.UUID, resource_slug: str) -> int:
        amount = await self.session.scalar(sa.select(sa.func.coalesce(sa.func.sum(DealResourceReservation.amount), 0)).where(DealResourceReservation.character_id == character_id, DealResourceReservation.resource_slug == resource_slug, DealResourceReservation.status == ResourceReservationStatus.ACTIVE))
        return int(amount or 0)

    async def mark_transferred_for_deal(self, deal_id: uuid.UUID) -> None:
        await self.session.execute(sa.update(DealResourceReservation).where(DealResourceReservation.deal_id == deal_id, DealResourceReservation.status == ResourceReservationStatus.ACTIVE).values(status=ResourceReservationStatus.TRANSFERRED))


class DealLedgerOperationRepository:
    model_type = DealLedgerOperation

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(self, operations: list[DealLedgerOperation]) -> None:
        self.session.add_all(operations)

    async def get_by_operation_id(self, operation_id: uuid.UUID) -> DealLedgerOperation | None:
        return await self.session.scalar(sa.select(DealLedgerOperation).where(DealLedgerOperation.operation_id == operation_id))


class TradeLicenseRepository:
    model_type = TradeLicense

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_character(self, character_id: uuid.UUID, for_update: bool = False) -> TradeLicense | None:
        statement = sa.select(TradeLicense).where(TradeLicense.character_id == character_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)   
