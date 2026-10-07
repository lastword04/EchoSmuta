"""Юнит-тесты AddDealInventoryItemUseCase: точные причины недоступности предмета.

Регресс на баг «предмет в лавке/на продаже → "Предмет не найден"»: у предмета
в лавке `InventoryItem.character_id == NULL` (строка принадлежит либо персонажу,
либо лавке), поэтому проверка владельца должна идти ПОСЛЕ `shop_id`.
"""

import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mining_app.apps.items.deals.enums import DealAssetType
from mining_app.apps.items.deals.exceptions import DealAssetUnavailableError
from mining_app.apps.items.deals.use_cases import AddDealInventoryItemUseCase
from mining_app.apps.items.enums import ItemBindingType, ItemType

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeSession,
    make_deal,
    make_offer,
    make_user,
)

USER = make_user(INIT_ID)


def _make_inventory_item(*, character_id=INIT_ID, shop_id=None, amount=1):
    return SimpleNamespace(
        id=uuid.uuid4(),
        character_id=character_id,
        shop_id=shop_id,
        item_slug="i.we.1.1.test-sword",
        amount=amount,
        expired_date=None,
        used_count=None,
        wear=0,
        item_binding_type=ItemBindingType.NONE,
        deal_id=None,
    )


def _make_item(is_stackable=False, can_sell=True, item_type=ItemType.WEAPON,
               location_slug="1.13.forge"):
    return SimpleNamespace(
        slug="i.we.1.1.test-sword",
        name="Тестовый меч",
        item_type=item_type,
        location_slug=location_slug,
        price=Decimal("15.00"), weight=10,
        race=None, minimal_level=0, parameters={}, ability_parameters={},
        is_stackable=is_stackable, can_sell=can_sell,
    )


def _build(*, inventory_item, item, equipped=False, for_sale=False):
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    my_offer.deal_id = deal.id
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_for_character(deal_id, cid, for_update=None):
        return my_offer

    async def get_by_deal(deal_id, for_update=None):
        return [partner_offer]

    async def inventory_for_trade(item_id, for_update=None):
        return inventory_item, item, equipped, for_sale

    repository = SimpleNamespace(session=FakeSession(), get_for_participant=get_for_participant)
    offer_repository = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    async def existing_items(deal_id, for_update=None):
        return []  # чужих предметов в сделке нет
    item_repository = SimpleNamespace(get_by_deal=existing_items, get_inventory_for_trade=inventory_for_trade)
    events = FakeEvents()
    use_case = AddDealInventoryItemUseCase(
        repository, offer_repository, item_repository, FakeCharacterClient([INIT_ID, PARTNER_ID]), events,
    )
    return use_case, events


async def _raises(use_case, expected_substring):
    with pytest.raises(DealAssetUnavailableError) as exc_info:
        await use_case(uuid.uuid4(), USER, SimpleNamespace(inventory_item_id=uuid.uuid4(), amount=1))
    assert expected_substring in exc_info.value.detail


@pytest.mark.asyncio
async def test_in_shop_raises_shop_message():
    """Предмет в лавке (character_id=NULL, shop_id задан) → «Предмет в лавке…», а не «не найден»."""
    use_case, _ = _build(
        inventory_item=_make_inventory_item(character_id=None, shop_id=uuid.uuid4()),
        item=_make_item(),
    )
    await _raises(use_case, "Предмет в лавке")


@pytest.mark.asyncio
async def test_for_sale_raises_sale_message():
    use_case, _ = _build(inventory_item=_make_inventory_item(), item=_make_item(), for_sale=True)
    await _raises(use_case, "Предмет на продаже")


@pytest.mark.asyncio
async def test_equipped_raises_equipped_message():
    use_case, _ = _build(inventory_item=_make_inventory_item(), item=_make_item(), equipped=True)
    await _raises(use_case, "Предмет надет")


@pytest.mark.asyncio
async def test_stranger_item_raises_not_found():
    """Чужой предмет (не в лавке, другой character_id) → «Предмет не найден»."""
    use_case, _ = _build(
        inventory_item=_make_inventory_item(character_id=PARTNER_ID),
        item=_make_item(),
    )
    await _raises(use_case, "Предмет не найден")


@pytest.mark.asyncio
async def test_normal_item_added():
    """Обычный предмет проходит все проверки и добавляется в сделку (событие UPDATED)."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    my_offer.deal_id = deal.id
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_for_character(deal_id, cid, for_update=None):
        return my_offer

    async def get_by_deal(deal_id, for_update=None):
        return [partner_offer]

    async def inventory_for_trade(item_id, for_update=None):
        return _make_inventory_item(), _make_item(), False, False

    repository = SimpleNamespace(session=FakeSession(), get_for_participant=get_for_participant)
    offer_repository = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    async def existing_items(deal_id, for_update=None):
        return []  # чужих предметов в сделке нет
    item_repository = SimpleNamespace(get_by_deal=existing_items, get_inventory_for_trade=inventory_for_trade)
    events = FakeEvents()
    use_case = AddDealInventoryItemUseCase(
        repository, offer_repository, item_repository, FakeCharacterClient([INIT_ID, PARTNER_ID]), events,
    )

    result = await use_case(deal.id, USER, SimpleNamespace(inventory_item_id=uuid.uuid4(), amount=1))

    assert result.asset_type == DealAssetType.INVENTORY_ITEM
    assert result.amount == 1
    assert events.published