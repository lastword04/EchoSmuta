import uuid
import pytest
from decimal import Decimal

from mining_app.apps.items.deals.use_cases import (
    SetDealDucatsUseCase,
)
from mining_app.apps.items.deals.exceptions import (
    DealMixedOfferError,
    DealBothSidesMoneyError,
)
from mining_app.apps.items.deals.enums import DealStatus


# ========== ФЕЙКИ (моки) ==========

class _Ctx:
    """Имитация async with session.begin()"""
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False

class FakeSession:
    def begin(self): return _Ctx()
    def add(self, *a, **k): pass

class FakeCharacterClient:
    def __init__(self, online_ids, ducats=Decimal('10000')):
        self.online_ids = online_ids
        self.ducats = ducats
    async def get_online_characters(self, location_slug):
        return type('R', (), {'objects': [type('C', (), {'id': i})() for i in self.online_ids]})()
    async def get_simple_character_balance(self, cid):
        return type('B', (), {'ducats': self.ducats, 'gold': Decimal('0')})()

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


def _build_use_case(my_items, partner_ducats=0, my_ducats=0):
    """Собирает SetDealDucatsUseCase с фейками"""
    deal = _make_deal()
    my_offer = _make_offer('init-id', my_ducats)
    partner_offer = _make_offer('partner-id', partner_ducats)

    repository = type('Repo', (), {
        'session': FakeSession(),
        'get_for_participant': (lambda *a, **k: _await(deal)),
    })()
    offer_repository = type('OfferRepo', (), {
        'get_for_character': (lambda *a, **k: _await(my_offer)),
        'get_by_deal': (lambda *a, **k: _await([my_offer, partner_offer])),
    })()
    item_repository = type('ItemRepo', (), {
        'get_by_deal': (lambda *a, **k: _await(my_items)),
    })()
    ledger_repository = type('Ledger', (), {
        'get_by_operation_id': (lambda *a, **k: _await(None)),
    })()
    client = FakeCharacterClient(['init-id', 'partner-id'])

    return SetDealDucatsUseCase(repository, offer_repository, item_repository, ledger_repository, client, None)


async def _await(value):
    return value


# ========== ТЕСТЫ ==========

@pytest.mark.asyncio
async def test_add_money_with_items_raises_mixed():
    """У меня уже есть товары → добавить деньги нельзя"""
    my_item = type('Item', (), {'owner_character_id': 'init-id'})()
    use_case = _build_use_case(my_items=[my_item])

    data = type('Data', (), {'operation_id': uuid.uuid4(), 'amount': Decimal('100')})()

    with pytest.raises(DealMixedOfferError):
        await use_case(uuid.uuid4(), type('U', (), {'character_id': 'init-id'})(), data)


@pytest.mark.asyncio
async def test_add_money_when_partner_has_money_raises():
    """У партнёра уже деньги → мне добавлять деньги нельзя"""
    use_case = _build_use_case(my_items=[], partner_ducats=500)

    data = type('Data', (), {'operation_id': uuid.uuid4(), 'amount': Decimal('100')})()

    with pytest.raises(DealBothSidesMoneyError):
        await use_case(uuid.uuid4(), type('U', (), {'character_id': 'init-id'})(), data)