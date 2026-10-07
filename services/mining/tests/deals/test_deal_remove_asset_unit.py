"""Юнит-тесты RemoveDealItemUseCase: удаление предметов/ресурсов из оффера."""
import uuid
from types import SimpleNamespace

import pytest

from shared.schemas.deal_events import DealEventType

from mining_app.apps.items.deals.enums import DealAssetType, ResourceReservationStatus
from mining_app.apps.items.deals.exceptions import DealAssetUnavailableError
from mining_app.apps.items.deals.use_cases import RemoveDealItemUseCase

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


def _build(deal, my_offer, partner_offer, *, deal_item=None, inventory_items=None, reservation=None):
    my_offer.deal_id = deal.id
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_for_character(deal_id, cid, for_update=None):
        return my_offer

    async def get_by_deal(deal_id, for_update=None):
        return [my_offer, partner_offer]

    async def get_for_deal_item(deal_id, item_id, for_update=None):
        return deal_item

    async def get_for_offer_asset(offer_id, asset_type, slug, for_update=None):
        return deal_item

    repository = SimpleNamespace(session=FakeSession(gets=inventory_items or {}), get_for_participant=get_for_participant)
    offer_repo = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_for_deal_item=get_for_deal_item, get_for_offer_asset=get_for_offer_asset)
    events = FakeEvents()
    use_case = RemoveDealItemUseCase(
        repository, offer_repo, item_repo, FakeReservationRepo(active=reservation),
        FakeCharacterClient([INIT_ID, PARTNER_ID]), events,
    )
    return use_case, events, repository


@pytest.mark.asyncio
async def test_remove_inventory_item_releases_and_resets():
    """Удаление предмета: deal_id инвентарной строки очищен, DealItem удалён, подтверждения сброшены."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, confirmed=1)
    inv = SimpleNamespace(id=uuid.uuid4(), deal_id=deal.id)
    deal_item = make_deal_item(INIT_ID, my_offer.id, inventory_item_id=inv.id)
    use_case, events, repository = _build(
        deal, my_offer, partner_offer, deal_item=deal_item, inventory_items={inv.id: inv},
    )

    await use_case(deal.id, deal_item.id, USER)

    assert inv.deal_id is None
    assert deal_item in repository.session.deleted
    assert partner_offer.confirmed_revision is None
    assert my_offer.revision == 2
    assert events.published[-1].event_type == DealEventType.UPDATED


@pytest.mark.asyncio
async def test_remove_resource_item_releases_reservation():
    """Удаление ресурса из оффера: резервация переводится в RELEASED."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    deal_item = make_deal_item(INIT_ID, my_offer.id, asset_type=DealAssetType.RESOURCE, resource_slug="iron", amount=10)
    reservation = SimpleNamespace(status=ResourceReservationStatus.ACTIVE)
    use_case, *_ = _build(deal, my_offer, partner_offer, deal_item=deal_item, reservation=reservation)

    await use_case(deal.id, deal_item.id, USER)

    assert reservation.status == ResourceReservationStatus.RELEASED


@pytest.mark.asyncio
async def test_remove_foreign_or_missing_item_raises():
    """Чужой/несуществующий DealItem удалить нельзя."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    use_case, *_ = _build(deal, my_offer, make_offer(PARTNER_ID, ducats=600), deal_item=None)

    with pytest.raises(DealAssetUnavailableError):
        await use_case(deal.id, uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_remove_resource_not_in_offer_raises():
    """Попытка убрать ресурс, которого нет в оффере."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    use_case, *_ = _build(deal, my_offer, make_offer(PARTNER_ID, ducats=600), deal_item=None)

    with pytest.raises(DealAssetUnavailableError):
        await use_case.remove_resource(deal.id, "gold_ore", USER)
