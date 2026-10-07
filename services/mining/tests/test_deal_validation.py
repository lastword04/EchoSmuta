import uuid
import pytest
from decimal import Decimal

from mining_app.apps.items.deals.use_cases import (
    _validate_deal_economy,
    _goods_value,
    _operation_id,
    _DealUseCase,
)
from mining_app.apps.items.deals.exceptions import (
    DealPriceTooLowError,
    DealBothSidesGoodsError,
    DealBothSidesMoneyError,
    DealMixedOfferError,
    DealNoMoneySideError,
)


# ========== ХЕЛПЕРЫ ==========

def _make_deal():
    return type('Deal', (), {
        'initiator_character_id': 'init-id',
        'partner_character_id': 'partner-id',
    })()


def _make_offer(character_id, ducats=0, gold=0):
    return type('Offer', (), {
        'character_id': character_id,
        'ducats_escrowed': Decimal(str(ducats)),
        'gold_escrowed': Decimal(str(gold)),
    })()


def _make_item(owner, asset_type, slug=None, resource_slug=None, amount=1):
    return type('Item', (), {
        'owner_character_id': owner,
        'asset_type': asset_type,
        'item_snapshot': {'item_slug': slug} if slug else {},
        'resource_slug': resource_slug,
        'amount': amount,
    })()


# ========== ВАЛИДАЦИЯ СДЕЛКИ ==========

def test_valid_deal_600_for_1000():
    _validate_deal_economy(
        _make_deal(),
        [_make_offer('init-id'), _make_offer('partner-id', ducats=600)],
        [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
        {'sword': Decimal('1000')}, {},
    )


def test_deal_too_cheap_100_for_1000():
    with pytest.raises(DealPriceTooLowError):
        _validate_deal_economy(
            _make_deal(),
            [_make_offer('init-id'), _make_offer('partner-id', ducats=100)],
            [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
            {'sword': Decimal('1000')}, {},
        )


def test_exact_boundary_500_for_1000():
    _validate_deal_economy(
        _make_deal(),
        [_make_offer('init-id'), _make_offer('partner-id', ducats=500)],
        [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
        {'sword': Decimal('1000')}, {},
    )


def test_both_sides_goods():
    with pytest.raises(DealBothSidesGoodsError):
        _validate_deal_economy(
            _make_deal(),
            [_make_offer('init-id'), _make_offer('partner-id', ducats=100)],
            [
                _make_item('init-id', 'INVENTORY_ITEM', slug='sword'),
                _make_item('partner-id', 'INVENTORY_ITEM', slug='shield'),
            ],
            {'sword': Decimal('1000'), 'shield': Decimal('500')}, {},
        )


def test_both_sides_money():
    with pytest.raises(DealBothSidesMoneyError):
        _validate_deal_economy(
            _make_deal(),
            [_make_offer('init-id', ducats=50), _make_offer('partner-id', ducats=600)],
            [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
            {'sword': Decimal('1000')}, {},
        )


def test_mixed_offer():
    with pytest.raises(DealMixedOfferError):
        _validate_deal_economy(
            _make_deal(),
            [_make_offer('init-id', ducats=100), _make_offer('partner-id')],
            [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
            {'sword': Decimal('1000')}, {},
        )


def test_no_money_side():
    with pytest.raises(DealNoMoneySideError):
        _validate_deal_economy(
            _make_deal(),
            [_make_offer('init-id'), _make_offer('partner-id')],
            [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
            {'sword': Decimal('1000')}, {},
        )


def test_gold_conversion():
    # 10 злт = 700 дт >= 500 → проходит
    _validate_deal_economy(
        _make_deal(),
        [_make_offer('init-id'), _make_offer('partner-id', gold=10)],
        [_make_item('init-id', 'INVENTORY_ITEM', slug='sword')],
        {'sword': Decimal('1000')}, {},
    )


# ========== РАСЧЁТ ЦЕННОСТИ ==========

def test_goods_value_items_only():
    items = [_make_item('a', 'INVENTORY_ITEM', slug='sword', amount=2)]
    assert _goods_value(items, {'sword': Decimal('1000')}, {}, 'a') == Decimal('2000')


def test_goods_value_resources_only():
    items = [_make_item('a', 'RESOURCE', resource_slug='iron', amount=100)]
    assert _goods_value(items, {}, {'iron': Decimal('1')}, 'a') == Decimal('100')


def test_goods_value_mixed_and_ignores_partner():
    items = [
        _make_item('a', 'INVENTORY_ITEM', slug='sword'),
        _make_item('a', 'RESOURCE', resource_slug='iron', amount=50),
        _make_item('b', 'INVENTORY_ITEM', slug='shield'),
    ]
    value = _goods_value(
        items,
        {'sword': Decimal('1000'), 'shield': Decimal('500')},
        {'iron': Decimal('1')},
        'a',
    )
    assert value == Decimal('1050')


def test_goods_value_unknown_slug_is_zero():
    items = [_make_item('a', 'INVENTORY_ITEM', slug='mystery', amount=3)]
    assert _goods_value(items, {}, {}, 'a') == Decimal('0')


# ========== СЛУЖЕБНАЯ ЛОГИКА ==========

def test_touch_offer_resets_confirmations():
    deal = type('Deal', (), {
        'expires_at': None,
        'cancelled_by_character_id': 'someone',
        'cancelled_at': 'something',
    })()
    offer = type('Offer', (), {'revision': 5, 'confirmed_revision': 5})()
    other = type('Offer', (), {'revision': 3, 'confirmed_revision': 3})()

    _DealUseCase._touch_offer(deal, offer, [offer, other])

    assert offer.revision == 6
    assert offer.confirmed_revision is None
    assert other.confirmed_revision is None
    assert deal.cancelled_by_character_id is None
    assert deal.cancelled_at is None
    assert deal.expires_at is not None


def test_operation_id_deterministic():
    deal_id = uuid.uuid4()
    assert _operation_id(deal_id, "income") == _operation_id(deal_id, "income")
    assert _operation_id(deal_id, "income") != _operation_id(deal_id, "tax")