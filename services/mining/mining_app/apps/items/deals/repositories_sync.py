import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session

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


class DealSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = Deal

    def get_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> Deal | None:
        stmt = sa.select(Deal).where(
            Deal.id == deal_id,
            sa.or_(Deal.initiator_character_id == character_id, Deal.partner_character_id == character_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.scalar(stmt)

    def get_for_update(self, deal_id: uuid.UUID) -> Deal | None:
        return self.session.scalar(sa.select(Deal).where(Deal.id == deal_id).with_for_update())

    def list_expired_for_update(self, now: datetime, limit: int) -> list[Deal]:
        stmt = (
            sa.select(Deal)
            .where(Deal.status.in_((DealStatus.DRAFT, DealStatus.ACTIVE)), Deal.expires_at <= now)
            .order_by(Deal.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self.session.scalars(stmt).all())

    def list_completing_for_update(self, limit: int) -> list[Deal]:
        stmt = (
            sa.select(Deal).where(Deal.status == DealStatus.COMPLETING)
            .order_by(Deal.updated_at).limit(limit).with_for_update(skip_locked=True)
        )
        return list(self.session.scalars(stmt).all())

    def list_completing(self, limit: int) -> list[Deal]:
        stmt = sa.select(Deal).where(Deal.status == DealStatus.COMPLETING).order_by(Deal.updated_at).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_detail_for_participant(self, deal_id: uuid.UUID, character_id: uuid.UUID) -> tuple[Deal, list[DealOffer], list[DealItem]] | None:
        stmt = (
            sa.select(Deal, DealOffer, DealItem)
            .outerjoin(DealOffer, DealOffer.deal_id == Deal.id)
            .outerjoin(DealItem, DealItem.deal_id == Deal.id)
            .where(
                Deal.id == deal_id,
                sa.or_(Deal.initiator_character_id == character_id, Deal.partner_character_id == character_id)
            )
        )
        rows = self.session.execute(stmt).all()
        if not rows:
            return None
        deal = rows[0].Deal
        offers = {offer.id: offer for _, offer, _ in rows if offer is not None}
        items = {item.id: item for _, _, item in rows if item is not None}
        return deal, list(offers.values()), list(items.values())


class DealOfferSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = DealOffer

    def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealOffer]:
        stmt = sa.select(DealOffer).where(DealOffer.deal_id == deal_id).order_by(DealOffer.created_at)
        if for_update:
            stmt = stmt.with_for_update()
        return list(self.session.scalars(stmt).all())

    def get_for_character(self, deal_id: uuid.UUID, character_id: uuid.UUID, for_update: bool = False) -> DealOffer | None:
        stmt = sa.select(DealOffer).where(DealOffer.deal_id == deal_id, DealOffer.character_id == character_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.scalar(stmt)


class DealItemSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = DealItem

    def get_by_deal(self, deal_id: uuid.UUID, for_update: bool = False) -> list[DealItem]:
        stmt = sa.select(DealItem).where(DealItem.deal_id == deal_id).order_by(DealItem.created_at)
        if for_update:
            stmt = stmt.with_for_update()
        return list(self.session.scalars(stmt).all())

    def clear_inventory_deal_id(self, deal_id: uuid.UUID) -> None:
        self.session.execute(sa.update(InventoryItem).where(InventoryItem.deal_id == deal_id).values(deal_id=None))

    def get_for_offer_asset(self, offer_id: uuid.UUID, asset_type: DealAssetType, resource_slug: str | None = None, for_update: bool = False) -> DealItem | None:
        stmt = sa.select(DealItem).where(DealItem.offer_id == offer_id, DealItem.asset_type == asset_type)
        if resource_slug is not None:
            stmt = stmt.where(DealItem.resource_slug == resource_slug)
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.scalar(stmt)

    def get_for_deal_item(self, deal_id: uuid.UUID, deal_item_id: uuid.UUID, for_update: bool = False) -> DealItem | None:
        stmt = sa.select(DealItem).where(DealItem.id == deal_item_id, DealItem.deal_id == deal_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.scalar(stmt)

    def get_inventory_for_trade(self, inventory_item_id: uuid.UUID, for_update: bool = False) -> tuple[InventoryItem, Item, bool, bool] | None:
        stmt = (
            sa.select(InventoryItem, Item, CharacterEquipment.id.is_not(None), SaleInventoryItem.id.is_not(None))
            .join(Item, Item.slug == InventoryItem.item_slug)
            .outerjoin(CharacterEquipment, CharacterEquipment.inventory_item_id == InventoryItem.id)
            .outerjoin(SaleInventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
            .where(InventoryItem.id == inventory_item_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        row = self.session.execute(stmt).one_or_none()
        return tuple(row) if row else None

    def incoming_weight(self, deal_id: uuid.UUID, recipient_id: uuid.UUID) -> int:
        owner_id = sa.case(
            (Deal.initiator_character_id == recipient_id, Deal.partner_character_id),
            else_=Deal.initiator_character_id,
        )
        inventory_weight = sa.select(sa.func.coalesce(sa.func.sum(DealItem.amount * Item.weight), 0)).join(
            InventoryItem, InventoryItem.id == DealItem.inventory_item_id
        ).join(
            Item, Item.slug == InventoryItem.item_slug
        ).join(
            Deal, Deal.id == DealItem.deal_id
        ).where(
            DealItem.deal_id == deal_id,
            DealItem.asset_type == DealAssetType.INVENTORY_ITEM,
            DealItem.owner_character_id == owner_id
        )
        resource_weight = sa.select(sa.func.coalesce(sa.func.sum(DealItem.amount * Resource.weight), 0)).join(
            Resource, Resource.slug == DealItem.resource_slug
        ).join(
            Deal, Deal.id == DealItem.deal_id
        ).where(
            DealItem.deal_id == deal_id,
            DealItem.asset_type == DealAssetType.RESOURCE,
            DealItem.owner_character_id == owner_id
        )
        return int(self.session.scalar(inventory_weight) or 0) + int(self.session.scalar(resource_weight) or 0)

    def transfer_assets(self, deal: Deal, items: list[DealItem]) -> None:
        for item in items:
            recipient_id = deal.partner_character_id if item.owner_character_id == deal.initiator_character_id else deal.initiator_character_id
            if item.asset_type == DealAssetType.INVENTORY_ITEM:
                inventory_item = self.session.get(InventoryItem, item.inventory_item_id, with_for_update=True)
                if inventory_item is None or inventory_item.deal_id != deal.id:
                    raise ValueError("Deal inventory item is no longer locked")
                inventory_item.character_id = recipient_id
                inventory_item.deal_id = None
                continue
            # resource
            source = self.session.scalar(
                sa.select(CharacterResource)
                .where(
                    CharacterResource.character_id == item.owner_character_id,
                    CharacterResource.resource_slug == item.resource_slug
                )
                .with_for_update()
            )
            if source is None or source.amount < item.amount:
                raise ValueError("Reserved resource is no longer available")
            target = self.session.scalar(
                sa.select(CharacterResource)
                .where(
                    CharacterResource.character_id == recipient_id,
                    CharacterResource.resource_slug == item.resource_slug
                )
                .with_for_update()
            )
            source.amount -= item.amount
            if target is None:
                self.session.add(
                    CharacterResource(
                        character_id=recipient_id,
                        resource_slug=item.resource_slug,
                        amount=item.amount
                    )
                )
            else:
                target.amount += item.amount


class DealResourceReservationSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = DealResourceReservation

    def release_active_for_deal(self, deal_id: uuid.UUID) -> None:
        self.session.execute(
            sa.update(DealResourceReservation)
            .where(
                DealResourceReservation.deal_id == deal_id,
                DealResourceReservation.status == ResourceReservationStatus.ACTIVE
            )
            .values(status=ResourceReservationStatus.RELEASED)
        )

    def get_active_for_item(self, deal_item_id: uuid.UUID, for_update: bool = False) -> DealResourceReservation | None:
        stmt = sa.select(DealResourceReservation).where(
            DealResourceReservation.deal_item_id == deal_item_id,
            DealResourceReservation.status == ResourceReservationStatus.ACTIVE
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.scalar(stmt)

    def reserved_amount(self, character_id: uuid.UUID, resource_slug: str) -> int:
        amount = self.session.scalar(
            sa.select(sa.func.coalesce(sa.func.sum(DealResourceReservation.amount), 0))
            .where(
                DealResourceReservation.character_id == character_id,
                DealResourceReservation.resource_slug == resource_slug,
                DealResourceReservation.status == ResourceReservationStatus.ACTIVE
            )
        )
        return int(amount or 0)

    def mark_transferred_for_deal(self, deal_id: uuid.UUID) -> None:
        self.session.execute(
            sa.update(DealResourceReservation)
            .where(
                DealResourceReservation.deal_id == deal_id,
                DealResourceReservation.status == ResourceReservationStatus.ACTIVE
            )
            .values(status=ResourceReservationStatus.TRANSFERRED)
        )


class DealLedgerOperationSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = DealLedgerOperation

    def create_many(self, operations: list[DealLedgerOperation]) -> None:
        self.session.add_all(operations)

    def get_by_operation_id(self, operation_id: uuid.UUID) -> DealLedgerOperation | None:
        return self.session.scalar(sa.select(DealLedgerOperation).where(DealLedgerOperation.operation_id == operation_id))


class TradeLicenseSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = TradeLicense

    def get_for_character(self, character_id: uuid.UUID, for_update: bool = False) -> TradeLicense | None:
        from sqlalchemy import text
        
        # Сначала пробуем ORM
        stmt = sa.select(TradeLicense).where(TradeLicense.character_id == character_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = self.session.scalar(stmt)
        
        if result is not None:
            return result
        
        # Fallback: raw SQL (если ORM не находит)
        raw_result = self.session.execute(
            text("SELECT character_id, end_date, id, updated_at, created_at FROM trade_licenses WHERE character_id = :cid"),
            {"cid": str(character_id)}
        )
        row = raw_result.fetchone()
        
        if row is None:
            return None
        
        # Создаём объект в detached состоянии (не привязываем к сессии)
        return TradeLicense(
            character_id=row[0],
            end_date=row[1],
            id=row[2],
            updated_at=row[3],
            created_at=row[4]
        )