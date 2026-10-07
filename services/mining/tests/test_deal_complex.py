import uuid
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from hypothesis import given, settings, strategies as st

from mining_app.apps.items.deals.use_cases import (
    _validate_deal_economy,
    _goods_value,
    ConfirmDealUseCase,
)
from mining_app.apps.items.deals.exceptions import (
    DealPriceTooLowError,
    DealNoMoneySideError,
)
from mining_app.apps.items.deals.enums import DealStatus

INIT_ID = uuid.uuid4()
PARTNER_ID = uuid.uuid4()


# ========== ФУЗЗИНГ: ПРАВИЛО ЦЕНЫ ==========

@given(
    price_cents=st.integers(min_value=1, max_value=10_000_00),
    amount=st.integers(min_value=1, max_value=100),
    money_cents=st.integers(min_value=0, max_value=10_000_00),
)
@settings(max_examples=300)
def test_fuzz_price_rule(price_cents, amount, money_cents):
    """300 случайных комбинаций: цена/кол-во/деньги"""
    price = Decimal(price_cents) / 100
    money = Decimal(money_cents) / 100

    deal = type('Deal', (), {'initiator_character_id': INIT_ID, 'partner_character_id': PARTNER_ID})()
    offers = [
        type('O', (), {'character_id': INIT_ID, 'ducats_escrowed': Decimal('0'), 'gold_escrowed': Decimal('0')})(),
        type('O', (), {'character_id': PARTNER_ID, 'ducats_escrowed': money, 'gold_escrowed': Decimal('0')})(),
    ]
    items = [type('I', (), {
        'owner_character_id': INIT_ID, 'asset_type': 'INVENTORY_ITEM',
        'item_snapshot': {'item_slug': 'x'}, 'amount': amount,
    })()]
    item_prices = {'x': price}

    min_price = price * amount * Decimal('0.5')

    if money <= 0:
        # Никто не дал деньги → отдельная ошибка (стоит раньше проверки цены)
        with pytest.raises(DealNoMoneySideError):
            _validate_deal_economy(deal, offers, items, item_prices, {})
    elif money >= min_price:
        _validate_deal_economy(deal, offers, items, item_prices, {})
    else:
        with pytest.raises(DealPriceTooLowError):
            _validate_deal_economy(deal, offers, items, item_prices, {})


# ========== ФУЗЗИНГ: РАСЧЁТ ЦЕННОСТИ ==========

@given(
    data=st.lists(
        st.tuples(
            st.sampled_from(['a', 'b']),
            st.sampled_from(['s1', 's2', 'r1']),
            st.integers(min_value=1, max_value=10),
        ),
        min_size=0, max_size=10,
    ),
)
@settings(max_examples=300)
def test_fuzz_goods_value(data):
    """300 случайных бандлов: ценность = сумма своих amount*price"""
    prices = {'s1': Decimal('100'), 's2': Decimal('50')}
    res_prices = {'r1': Decimal('1')}

    items = [type('I', (), {
        'owner_character_id': owner,
        'asset_type': 'RESOURCE' if slug == 'r1' else 'INVENTORY_ITEM',
        'item_snapshot': {'item_slug': slug} if slug != 'r1' else {},
        'resource_slug': slug if slug == 'r1' else None,
        'amount': amount,
    })() for owner, slug, amount in data]

    expected = Decimal('0')
    for owner, slug, amount in data:
        if owner != 'a':
            continue
        if slug == 'r1':
            expected += res_prices[slug] * amount
        else:
            expected += prices[slug] * amount

    got = _goods_value(items, prices, res_prices, 'a')
    assert got == expected


# ========== ПОЛНЫЙ ЖИЗНЕННЫЙ ЦИКЛ ==========

class _Ctx:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False

class _Result:
    def __init__(self, rows): self._rows = rows
    def all(self): return self._rows

class FakeSession:
    def __init__(self, rows=None): self._rows = rows or []
    def begin(self): return _Ctx()
    def add(self, *a, **k): pass
    async def execute(self, *a, **k): return _Result(self._rows)

class FakeCharacterClient:
    def __init__(self, online_ids):
        self.online_ids = online_ids
    async def get_online_characters(self, slug):
        return type('R', (), {'objects': [type('C', (), {'id': i})() for i in self.online_ids]})()
    async def get_character_weight_balance(self, cid):
        return type('B', (), {'weight': 0, 'max_weight': 100})()

async def _await(v): return v

def _make_deal():
    now = datetime.now(timezone.utc)
    return type('Deal', (), {
        'id': uuid.uuid4(), 'status': DealStatus.ACTIVE,
        'initiator_character_id': INIT_ID, 'partner_character_id': PARTNER_ID,
        'location_slug': '1.13.forge', 'expires_at': now + timedelta(minutes=30),
        'cancelled_by_character_id': None, 'cancelled_at': None,
        'created_at': now, 'updated_at': now, 'completed_at': None,
        'initiator_confirmed_at': None, 'partner_confirmed_at': None,
    })()

def _make_offer(cid, ducats=0):
    return type('Offer', (), {
        'character_id': cid, 'ducats_amount': Decimal('0'),
        'ducats_escrowed': Decimal(str(ducats)), 'gold_amount': Decimal('0'),
        'gold_escrowed': Decimal('0'), 'revision': 1, 'confirmed_revision': None,
    })()

def _item(owner, slug='sword', amount=1):
    return type('Item', (), {
        'owner_character_id': owner, 'asset_type': 'INVENTORY_ITEM',
        'item_snapshot': {'item_slug': slug}, 'resource_slug': None, 'amount': amount,
    })()

PRICES = [('sword', Decimal('1000'))]


@pytest.mark.asyncio
async def test_lifecycle_both_confirm_triggers_complete():
    """Оба подтверждают → вызывается завершение сделки"""
    completed = {'called': False}

    async def fake_complete(deal_id):
        completed['called'] = True
        return None

    deal = _make_deal()
    init_offer = _make_offer(INIT_ID)
    partner_offer = _make_offer(PARTNER_ID, 600)
    items = [_item(INIT_ID)]

    repository = type('Repo', (), {
        'session': FakeSession(PRICES),
        'get_for_participant': lambda *a, **k: _await(deal),
    })()
    offer_repository = type('OR', (), {
        'get_by_deal': lambda *a, **k: _await([init_offer, partner_offer]),
    })()
    item_repository = type('IR', (), {
        'get_by_deal': lambda *a, **k: _await(items),
        'incoming_weight': lambda *a, **k: _await(0),
    })()
    client = FakeCharacterClient([INIT_ID, PARTNER_ID])

    use_case = ConfirmDealUseCase(repository, offer_repository, item_repository, fake_complete, client, None)

    user_init = type('U', (), {'character_id': INIT_ID})()
    user_part = type('U', (), {'character_id': PARTNER_ID})()

    # 1) Инициатор подтверждает — завершение НЕ вызывается
    await use_case(uuid.uuid4(), user_init)
    assert not completed['called']
    assert init_offer.confirmed_revision == init_offer.revision

    # 2) Партнёр подтверждает — завершение ВЫЗЫВАЕТСЯ
    await use_case(uuid.uuid4(), user_part)
    assert completed['called']
    assert partner_offer.confirmed_revision == partner_offer.revision