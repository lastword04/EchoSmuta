import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import PaginationCharacterSimpleInfoReadSchema
from shared.schemas.deal_events import DealEventSchema, DealEventType

from .....resources.models import Resource
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ....models import Item
from ...enums import DealAssetType, DealStatus
from ...exceptions import (
    DealAccessDeniedError,
    DealBothSidesGoodsError,
    DealBothSidesMoneyError,
    DealEmptyOfferError,
    DealMixedOfferError,
    DealNoMoneySideError,
    DealNotFoundError,
    DealPriceTooLowError,
    DealProximityError,
    DealStateError,
)
from ...models import Deal, DealItem, DealOffer
from ...repositories import DealOfferRepositoryProtocol, DealRepositoryProtocol

logger = logging.getLogger(__name__)

DEAL_LIFETIME = timedelta(minutes=30)
GOLD_TO_DUCATS = Decimal(70)        # 1 злт = 70 дт (нижняя граница)
MIN_DEAL_VALUE_RATIO = Decimal("0.5") # продавец получает >= 50% стоимости товаров
_OPERATION_NAMESPACE = uuid.UUID("1bdbf5e3-82c8-43ee-89fb-6b794ce1ebbd")
DEAL_ALLOWED_LOCATION_SLUGS = frozenset([
    '1.13.forge',       # кузница
    '1.16.jewelers',    # ювелирная
])


def _character_id(user: UserTokenDataReadSchema) -> uuid.UUID:
    if not user.character_id:
        raise DealAccessDeniedError()
    return user.character_id


def _operation_id(deal_id: uuid.UUID, name: str) -> uuid.UUID:
    return uuid.uuid5(_OPERATION_NAMESPACE, f"{deal_id}:{name}")



async def _publish_deal_event(
    deal_events: DealEventsProtocol,
    deal: Deal,
    event_type: DealEventType,
    details: dict | None = None,
) -> None:
    """Шлёт ОДНО событие (chat-сервис сам решит кому отправить)."""
    try:
        await deal_events.publish_deal_event(
            DealEventSchema(
                event_type=event_type,
                deal_id=deal.id,
                character_id=deal.initiator_character_id,  # отправитель
                initiator_character_id=deal.initiator_character_id,
                partner_character_id=deal.partner_character_id,
                location_slug=deal.location_slug,
                details=details,
            )
        )
    except Exception as e:
        logger.warning("Failed to publish deal event %s: %s", event_type, e)


async def _goods_prices(session: AsyncSession, items: Sequence[DealItem]) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    item_slugs = {
        it.item_snapshot.get("item_slug")
        for it in items
        if it.asset_type == DealAssetType.INVENTORY_ITEM and it.item_snapshot.get("item_slug")
    }
    item_prices = {}
    if item_slugs:
        rows = await session.execute(sa.select(Item.slug, Item.price).where(Item.slug.in_(item_slugs)))
        item_prices = {slug: Decimal(str(price)) for slug, price in rows.all()}

    resource_slugs = {it.resource_slug for it in items if it.asset_type == DealAssetType.RESOURCE and it.resource_slug}
    resource_prices = {}
    if resource_slugs:
        rows = await session.execute(sa.select(Resource.slug, Resource.price).where(Resource.slug.in_(resource_slugs)))
        resource_prices = {slug: Decimal(str(price)) for slug, price in rows.all()}
    return item_prices, resource_prices


def _goods_value(items: Sequence[DealItem], item_prices: dict[str, Decimal], resource_prices: dict[str, Decimal], character_id: uuid.UUID) -> Decimal:
    total = Decimal(0)
    for it in items:
        if it.owner_character_id != character_id:
            continue
        if it.asset_type == DealAssetType.INVENTORY_ITEM:
            total += item_prices.get(it.item_snapshot.get("item_slug"), Decimal(0)) * it.amount
        elif it.asset_type == DealAssetType.RESOURCE:
            total += resource_prices.get(it.resource_slug, Decimal(0)) * it.amount
    return total


def _validate_deal_economy(deal: Deal, offers: Sequence[DealOffer], items: Sequence[DealItem], item_prices: dict[str, Decimal], resource_prices: dict[str, Decimal]) -> None:
    init_offer = next(o for o in offers if o.character_id == deal.initiator_character_id)
    part_offer = next(o for o in offers if o.character_id == deal.partner_character_id)
    init_money = init_offer.ducats_escrowed + init_offer.gold_escrowed * GOLD_TO_DUCATS
    part_money = part_offer.ducats_escrowed + part_offer.gold_escrowed * GOLD_TO_DUCATS
    init_goods = _goods_value(items, item_prices, resource_prices, deal.initiator_character_id)
    part_goods = _goods_value(items, item_prices, resource_prices, deal.partner_character_id)

    if init_money > 0 and part_money > 0:
        raise DealBothSidesMoneyError()
    if init_goods > 0 and part_goods > 0:
        raise DealBothSidesGoodsError()

    if init_goods > 0:
        seller_goods, seller_money, buyer_money, buyer_goods = init_goods, init_money, part_money, part_goods
    else:
        seller_goods, seller_money, buyer_money, buyer_goods = part_goods, part_money, init_money, init_goods

    if seller_money > 0 or buyer_goods > 0:
        raise DealMixedOfferError()
    if seller_goods <= 0:
        raise DealEmptyOfferError()
    if buyer_money <= 0:
        raise DealNoMoneySideError()
    if buyer_money < seller_goods * MIN_DEAL_VALUE_RATIO:
        raise DealPriceTooLowError()


class _DealUseCase:
    def __init__(self, character_client: CharacterServiceClientProtocol) -> None:
        self.character_client = character_client

    async def _online_at_location(self, location_slug: str) -> PaginationCharacterSimpleInfoReadSchema:
        return await self.character_client.get_online_characters(location_slug)

    async def _ensure_proximity(self, initiator_id: uuid.UUID, partner_id: uuid.UUID, location_slug: str) -> None:
        online = await self._online_at_location(location_slug)
        online_ids = {character.id for character in online.objects}
        if initiator_id not in online_ids or partner_id not in online_ids:
            raise DealProximityError()

    async def _prepare_offer(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, deal_id: uuid.UUID, character_id: uuid.UUID) -> tuple[Deal, DealOffer]:
        deal = await repository.get_for_participant(deal_id, character_id, for_update=True)
        if not deal:
            raise DealNotFoundError(deal_id)
        if deal.status not in (DealStatus.DRAFT, DealStatus.ACTIVE):
            raise DealStateError("Only draft or active deals can be edited")
        await self._ensure_proximity(deal.initiator_character_id, deal.partner_character_id, deal.location_slug)
        offer = await offer_repository.get_for_character(deal.id, character_id, for_update=True)
        if not offer:
            raise DealAccessDeniedError()
        return deal, offer

    @staticmethod
    def _touch_offer(deal: Deal, offer: DealOffer, offers: list[DealOffer]) -> None:
        offer.revision += 1
        for current_offer in offers:
            current_offer.confirmed_revision = None
        deal.expires_at = datetime.now(UTC) + DEAL_LIFETIME
        # Если кто-то добавил/убрал предмет или деньги — значит "передумал" отменять
        deal.cancelled_by_character_id = None
        deal.cancelled_at = None
