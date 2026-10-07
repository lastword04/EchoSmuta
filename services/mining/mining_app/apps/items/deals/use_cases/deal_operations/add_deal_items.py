import uuid
from typing import Protocol

import sqlalchemy as sa

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from .....resources.models import CharacterResource, Resource
from ....adapters.characters import CharacterServiceClientProtocol
from ....enums import ItemBindingType
from ....events.deals import DealEventsProtocol
from ....models import InventoryItem
from ...enums import (
    TRADEABLE_ITEM_TYPES,
    DealAssetType,
    ResourceReservationStatus,
)
from ...exceptions import (
    DealAssetUnavailableError,
    DealBothSidesGoodsError,
    DealMixedOfferError,
)
from ...models import DealItem, DealResourceReservation
from ...repositories import (
    DealItemRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
    DealResourceReservationRepositoryProtocol,
)
from ...schemas import (
    DealInventoryItemOfferCreateSchema,
    DealItemReadSchema,
    DealResourceOfferUpdateSchema,
)
from ._base import (
    DEAL_ALLOWED_LOCATION_SLUGS,
    _character_id,
    _DealUseCase,
    _publish_deal_event,
)


class AddDealResourceUseCaseProtocol(UseCaseProtocol[DealItemReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, resource_slug: str, user: UserTokenDataReadSchema, data: DealResourceOfferUpdateSchema) -> DealItemReadSchema: ...


class AddDealResourceUseCase(_DealUseCase, AddDealResourceUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, reservation_repository: DealResourceReservationRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository, self.offer_repository = repository, offer_repository
        self.item_repository, self.reservation_repository = item_repository, reservation_repository
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, resource_slug: str, user: UserTokenDataReadSchema, data: DealResourceOfferUpdateSchema) -> DealItemReadSchema:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            deal, offer = await self._prepare_offer(self.repository, self.offer_repository, deal_id, character_id)
            if offer.ducats_escrowed > 0 or offer.gold_escrowed > 0:
                raise DealMixedOfferError()
            existing_items = await self.item_repository.get_by_deal(deal.id)
            if any(it.owner_character_id != character_id for it in existing_items):
                raise DealBothSidesGoodsError()
            resource = await self.repository.session.scalar(sa.select(CharacterResource).where(CharacterResource.character_id == character_id, CharacterResource.resource_slug == resource_slug).with_for_update())
            reserved = await self.reservation_repository.reserved_amount(character_id, resource_slug)
            existing_item = await self.item_repository.get_for_offer_asset(offer.id, DealAssetType.RESOURCE, resource_slug, for_update=True)
            previous = existing_item.amount if existing_item else 0
            if not resource or resource.amount - reserved + previous < data.amount:
                raise DealAssetUnavailableError("Insufficient available resource amount")
            resource_meta = await self.repository.session.scalar(sa.select(Resource).where(Resource.slug == resource_slug))
            snapshot = {
                "resource_slug": resource_slug,
                "name": resource_meta.name if resource_meta else resource_slug,
                "amount": data.amount,
                "price": float(resource_meta.price) if resource_meta and resource_meta.price is not None else 0,
                "weight": int(resource_meta.weight) if resource_meta and resource_meta.weight is not None else 0,
            }
            if existing_item:
                existing_item.amount = data.amount
                existing_item.item_snapshot = snapshot
                reservation = await self.reservation_repository.get_active_for_item(existing_item.id, for_update=True)
                if reservation:
                    reservation.amount = data.amount
                deal_item = existing_item
            else:
                deal_item = DealItem(deal_id=deal.id, offer_id=offer.id, owner_character_id=character_id, asset_type=DealAssetType.RESOURCE, resource_slug=resource_slug, amount=data.amount, item_snapshot=snapshot)
                self.repository.session.add(deal_item)
                await self.repository.session.flush()
                self.repository.session.add(DealResourceReservation(deal_id=deal.id, deal_item_id=deal_item.id, character_id=character_id, resource_slug=resource_slug, amount=data.amount, status=ResourceReservationStatus.ACTIVE))
            self._touch_offer(deal, offer, await self.offer_repository.get_by_deal(deal.id, for_update=True))
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"asset": "resource", "resource_slug": resource_slug})
        return DealItemReadSchema.model_validate(deal_item)


class AddDealInventoryItemUseCaseProtocol(UseCaseProtocol[DealItemReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema, data: DealInventoryItemOfferCreateSchema) -> DealItemReadSchema: ...


class AddDealInventoryItemUseCase(_DealUseCase, AddDealInventoryItemUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository, self.offer_repository, self.item_repository = repository, offer_repository, item_repository
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema, data: DealInventoryItemOfferCreateSchema) -> DealItemReadSchema:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            deal, offer = await self._prepare_offer(self.repository, self.offer_repository, deal_id, character_id)
            # 🎭 Роли: у кого деньги — не кидает товары; товары только с одной стороны
            if offer.ducats_escrowed > 0 or offer.gold_escrowed > 0:
                raise DealMixedOfferError()
            existing_items = await self.item_repository.get_by_deal(deal.id)
            if any(it.owner_character_id != character_id for it in existing_items):
                raise DealBothSidesGoodsError()
            row = await self.item_repository.get_inventory_for_trade(data.inventory_item_id, for_update=True)
            if not row:
                raise DealAssetUnavailableError("Предмет не найден")
            inventory_item, item, equipped, for_sale = row
            # 📋 Последовательные проверки доступности: каждая причина — со своим
            # понятным игроку сообщением.
            # ⚠️ Предмет в лавке имеет character_id = NULL (инвентарная строка
            # принадлежит ЛИБО персонажу, ЛИБО лавке), поэтому лавку диагностируем
            # ДО проверки владельца — иначе предмет в лавке ошибочно отклонялся
            # как «Предмет не найден».
            if inventory_item.shop_id:
                raise DealAssetUnavailableError("Предмет в лавке — сначала забери его оттуда")
            if inventory_item.character_id != character_id:
                raise DealAssetUnavailableError("Предмет не найден")
            if inventory_item.deal_id:
                raise DealAssetUnavailableError("Предмет уже находится в сделке")
            if equipped:
                raise DealAssetUnavailableError("Предмет надет — сначала сними его")
            if for_sale:
                raise DealAssetUnavailableError("Предмет на продаже — сначала сними с продажи")
            if inventory_item.item_binding_type != ItemBindingType.NONE:
                raise DealAssetUnavailableError("Привязанный предмет нельзя передать")
            if item.item_type not in TRADEABLE_ITEM_TYPES:
                raise DealAssetUnavailableError("Этот тип предмета нельзя передать в сделке")
            if item.location_slug not in DEAL_ALLOWED_LOCATION_SLUGS:
                raise DealAssetUnavailableError("Этот предмет нельзя передать в сделку в данной локации")
            if not item.can_sell:
                raise DealAssetUnavailableError("Этот предмет нельзя продавать")
            if data.amount > inventory_item.amount:
                raise DealAssetUnavailableError("Недостаточно предметов")
            if not item.is_stackable and data.amount != inventory_item.amount:
                raise DealAssetUnavailableError("Нестакбаемый предмет передаётся только целиком")
            if item.is_stackable and data.amount < inventory_item.amount:
                inventory_item.amount -= data.amount
                offered_item = InventoryItem(character_id=character_id, shop_id=None, deal_id=deal.id, item_slug=inventory_item.item_slug, amount=data.amount, expired_date=inventory_item.expired_date, used_count=inventory_item.used_count, wear=inventory_item.wear, item_binding_type=inventory_item.item_binding_type)
                self.repository.session.add(offered_item)
                await self.repository.session.flush()
            else:
                inventory_item.deal_id = deal.id
                offered_item = inventory_item
            deal_item = DealItem(
                deal_id=deal.id,
                offer_id=offer.id,
                owner_character_id=character_id,
                asset_type=DealAssetType.INVENTORY_ITEM,
                inventory_item_id=offered_item.id,
                amount=data.amount,
                item_snapshot={
                    "item_slug": item.slug,
                    "name": item.name,
                    "amount": data.amount,
                    "item_type": getattr(item.item_type, "value", item.item_type),
                    "price": float(item.price) if item.price is not None else 0,
                    "weight": item.weight or 0,
                    "minimal_level": item.minimal_level or 0,
                    "race": getattr(item.race, "value", item.race) if item.race is not None else None,
                    "wear": offered_item.wear or 0,
                    "expired_date": offered_item.expired_date.isoformat() if offered_item.expired_date else None,
                    "used_count": offered_item.used_count or 0,
                    "parameters": item.parameters or {},
                    "ability_parameters": item.ability_parameters or {},
                },
            )
            self.repository.session.add(deal_item)
            self._touch_offer(deal, offer, await self.offer_repository.get_by_deal(deal.id, for_update=True))
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"asset": "item", "item_slug": item.slug})
        return DealItemReadSchema.model_validate(deal_item)


