"""Юнит-тесты AddDealResourceUseCase: добавление ресурсов в оффер сделки."""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from shared.schemas.deal_events import DealEventType

from mining_app.apps.items.deals.enums import DealAssetType, ResourceReservationStatus
from mining_app.apps.items.deals.exceptions import (
    DealAssetUnavailableError,
    DealBothSidesGoodsError,
    DealMixedOfferError,
)
from mining_app.apps.items.deals.models import DealItem, DealResourceReservation
from mining_app.apps.items.deals.use_cases import AddDealResourceUseCase

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeReservationRepo,
    FakeSession,
    make_deal,
    make_deal_item,
    make_offer,
    make_user,
)

USER = make_user(INIT_ID)


def _build(deal, my_offer, partner_offer, *, existing_items=None, resource=None,
           resource_meta=None, existing_deal_item=None, reserved=0):
    my_offer.deal_id = deal.id
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_for_character(deal_id, cid, for_update=None):
        return my_offer

    async def get_by_deal(deal_id, for_update=None):
        return [my_offer, partner_offer]

    async def items_by_deal(deal_id):
        return existing_items or []

    async def get_for_offer_asset(offer_id, asset_type, slug, for_update=None):
        return existing_deal_item

    repository = SimpleNamespace(
        session=FakeSession(scalars=[resource, resource_meta]),
        get_for_participant=get_for_participant,
    )
    offer_repo = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_by_deal=items_by_deal, get_for_offer_asset=get_for_offer_asset)
    events = FakeEvents()
    use_case = AddDealResourceUseCase(
        repository, offer_repo, item_repo, FakeReservationRepo(reserved=reserved), FakeCharacterClient([INIT_ID, PARTNER_ID]), events,
    )
    return use_case, events, repository


@pytest.mark.asyncio
async def test_add_resource_success_creates_item_and_reservation():
    """Ресурс добавляется: DealItem + активная резервация, оффер touched, событие отправлено."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    resource = SimpleNamespace(amount=100)           # CharacterResource
    # Resource (для снапшота): name/price/weight читаются при построении item_snapshot
    resource_meta = SimpleNamespace(name="Железо", price=10, weight=2)
    use_case, events, repository = _build(
        deal, my_offer, partner_offer, resource=resource, resource_meta=resource_meta,
    )

    result = await use_case(deal.id, "iron", USER, SimpleNamespace(amount=5))

    assert result.amount == 5
    assert result.resource_slug == "iron"
    assert result.asset_type == DealAssetType.RESOURCE
    assert result.item_snapshot["name"] == "Железо"
    assert any(isinstance(obj, DealItem) for obj in repository.session.added)
    reservations = [obj for obj in repository.session.added if isinstance(obj, DealResourceReservation)]
    assert len(reservations) == 1
    assert reservations[0].status == ResourceReservationStatus.ACTIVE
    assert reservations[0].amount == 5
    assert my_offer.revision == 2
    assert events.published[-1].event_type == DealEventType.UPDATED


@pytest.mark.asyncio
async def test_add_resource_with_money_raises_mixed():
    """У меня уже эскроу-деньги → добавлять ресурсы нельзя."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID, ducats=100)
    use_case, *_ = _build(deal, my_offer, make_offer(PARTNER_ID), resource=SimpleNamespace(amount=100))

    with pytest.raises(DealMixedOfferError):
        await use_case(deal.id, "iron", USER, SimpleNamespace(amount=5))


@pytest.mark.asyncio
async def test_add_resource_when_partner_has_goods_raises():
    """У партнёра уже товары → мне добавлять ресурсы нельзя (бартер запрещён)."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    partner_item = make_deal_item(PARTNER_ID, partner_offer.id, snapshot={"item_slug": "shield"})
    use_case, *_ = _build(
        deal, my_offer, partner_offer,
        existing_items=[partner_item], resource=SimpleNamespace(amount=100),
    )

    with pytest.raises(DealBothSidesGoodsError):
        await use_case(deal.id, "iron", USER, SimpleNamespace(amount=5))


@pytest.mark.asyncio
async def test_add_resource_insufficient_raises():
    """Ресурса меньше запрошенного (с учётом резерваций) → DealAssetUnavailableError."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    use_case, *_ = _build(
        deal, my_offer, make_offer(PARTNER_ID, ducats=600),
        resource=SimpleNamespace(amount=3), reserved=0,
    )

    with pytest.raises(DealAssetUnavailableError):
        await use_case(deal.id, "iron", USER, SimpleNamespace(amount=5))
