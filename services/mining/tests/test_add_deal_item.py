import uuid
import pytest
from decimal import Decimal

from mining_app.apps.items.deals.use_cases import (
    AddDealInventoryItemUseCase,
)
from mining_app.apps.items.deals.exceptions import (
    DealMixedOfferError,
    DealBothSidesGoodsError,
)
from mining_app.apps.items.deals.enums import DealStatus


# ========== ФЕЙКИ (копия из test_set_deal_currency.py) ==========

class _Ctx:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False

class FakeSession:
    def begin(self): return _Ctx()
    def add(self, *a, **k): pass

class FakeCharacterClient:
    def __init__(self, online_ids):
        self.online_ids = online_ids
    async def get_online_characters(self, location_slug):
        return type('R', (), {'objects': [type('C', (), {'id': i})() for i in self.online_ids]})()

async def _await(value):
    return value

def _make_deal():
    return type('Deal', (), {
        'id': uuid.uuid4(),
        'status': DealStatus.ACTIVE,
        'initiator_character_id': 'init-id',
        'partner_character_id': 'partner-id',
        'location_slug': '1.13.forge',
        'expires_at': None,
        'cancelled_by_character_id': None,
        'cancelled_at': None,
    })()

def _make_offer(cid, ducats=0):
    return type('Offer', (), {
        'character_id': cid,
        'ducats_amount': Decimal('0'),
        'ducats_escrowed': Decimal(str(ducats)),
        'gold_amount': Decimal('0'),
        'gold_escrowed': Decimal('0'),
        'revision': 1,
        'confirmed_revision': None,
    })()

def _build(my_ducats=0, existing_items=None):
    deal = _make_deal()
    my_offer = _make_offer('init-id', my_ducats)
    repository = type('Repo', (), {
        'session': FakeSession(),
        'get_for_participant': (lambda *a, **k: _await(deal)),
    })()
    offer_repository = type('OfferRepo', (), {
        'get_for_character': (lambda *a, **k: _await(my_offer)),
    })()
    item_repository = type('ItemRepo', (), {
        'get_by_deal': (lambda *a, **k: _await(existing_items or [])),
    })()
    client = FakeCharacterClient(['init-id', 'partner-id'])
    return AddDealInventoryItemUseCase(repository, offer_repository, item_repository, client, None)


# ========== ТЕСТЫ ==========

@pytest.mark.asyncio
async def test_add_item_when_i_have_money_raises_mixed():
    """У меня уже деньги → добавить товар нельзя"""
    use_case = _build(my_ducats=100)
    data = type('Data', (), {'inventory_item_id': uuid.uuid4(), 'amount': 1})()
    user = type('U', (), {'character_id': 'init-id'})()

    with pytest.raises(DealMixedOfferError):
        await use_case(uuid.uuid4(), user, data)


@pytest.mark.asyncio
async def test_add_item_when_partner_has_goods_raises():
    """У партнёра уже товары → мне добавлять товары нельзя (бартер запрещён)"""
    partner_item = type('Item', (), {'owner_character_id': 'partner-id'})()
    use_case = _build(my_ducats=0, existing_items=[partner_item])
    data = type('Data', (), {'inventory_item_id': uuid.uuid4(), 'amount': 1})()
    user = type('U', (), {'character_id': 'init-id'})()

    with pytest.raises(DealBothSidesGoodsError):
        await use_case(uuid.uuid4(), user, data)