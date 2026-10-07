import uuid
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from mining_app.apps.items.deals.use_cases import (
    ConfirmDealUseCase,
)
from mining_app.apps.items.deals.exceptions import (
    DealEmptyOfferError,
    DealNotReadyError,
    DealPartnerDepartedError,
    DealPartnerOfflineError,
    DealSelfWeightLimitError,
    DealPartnerWeightLimitError,
)
from mining_app.apps.items.deals.enums import DealStatus


# ========== КОНСТАНТЫ ==========

INIT_ID = uuid.uuid4()
PARTNER_ID = uuid.uuid4()


# ========== ФЕЙКИ ==========

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
    def __init__(self, online_ids, balances=None, partner_location='1.13.forge'):
        self.online_ids = online_ids
        self.balances = balances or {}
        self.partner_location = partner_location

    async def get_online_characters(self, slug):
        return type('R', (), {'objects': [type('C', (), {'id': i})() for i in self.online_ids]})()

    async def get_full_character(self, cid):
        return type('FC', (), {'location_slug': self.partner_location})()

    async def get_character_weight_balance(self, cid):
        return self.balances.get(cid, type('B', (), {'weight': 0, 'max_weight': 100})())


async def _await(v): return v


def _make_deal(status=DealStatus.ACTIVE):
    now = datetime.now(timezone.utc)
    return type('Deal', (), {
        'id': uuid.uuid4(),
        'status': status,
        'initiator_character_id': INIT_ID,
        'partner_character_id': PARTNER_ID,
        'location_slug': '1.13.forge',
        'expires_at': now + timedelta(minutes=30),
        'cancelled_by_character_id': None,
        'cancelled_at': None,
        'created_at': now,
        'updated_at': now,
        'completed_at': None,
        'initiator_confirmed_at': None,
        'partner_confirmed_at': None,
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


def _item(owner, slug='sword', amount=1):
    return type('Item', (), {
        'owner_character_id': owner,
        'asset_type': 'INVENTORY_ITEM',
        'item_snapshot': {'item_slug': slug},
        'resource_slug': None,
        'amount': amount,
    })()


PRICES = [('sword', Decimal('1000')), ('iron', Decimal('1'))]
USER = type('U', (), {'character_id': INIT_ID})()


def _build(my_offer, partner_offer, items, online_ids, balances=None,
           status=DealStatus.ACTIVE, partner_location='1.13.forge', incoming=None):
    deal = _make_deal(status)
    repository = type('Repo', (), {
        'session': FakeSession(PRICES),
        'get_for_participant': lambda *a, **k: _await(deal),
    })()
    offer_repository = type('OR', (), {
        'get_by_deal': lambda *a, **k: _await([my_offer, partner_offer]),
    })()
    incoming = incoming or {}
    item_repository = type('IR', (), {
        'get_by_deal': lambda *a, **k: _await(items),
        'incoming_weight': lambda *a, **k: _await(incoming.get(a[-1], 0)),
    })()
    client = FakeCharacterClient(online_ids, balances, partner_location)
    return ConfirmDealUseCase(repository, offer_repository, item_repository, None, client, None), deal


# ========== ТЕСТЫ ==========

@pytest.mark.asyncio
async def test_confirm_empty_offer():
    """Моё предложение пустое → ошибка"""
    use_case, _ = _build(_make_offer(INIT_ID), _make_offer(PARTNER_ID), [], [INIT_ID, PARTNER_ID])
    with pytest.raises(DealEmptyOfferError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_partner_departed():
    """Партнёр ушёл из локации → ошибка"""
    use_case, _ = _build(
        _make_offer(INIT_ID, 600), _make_offer(PARTNER_ID),
        [_item(PARTNER_ID)], [INIT_ID], partner_location='9.99.other',
    )
    with pytest.raises(DealPartnerDepartedError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_partner_offline():
    """Партнёр в локации, но оффлайн → ошибка"""
    use_case, _ = _build(
        _make_offer(INIT_ID, 600), _make_offer(PARTNER_ID),
        [_item(PARTNER_ID)], [INIT_ID],
    )
    with pytest.raises(DealPartnerOfflineError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_not_ready_when_draft():
    """Сделка не принята (DRAFT) → ошибка"""
    use_case, _ = _build(
        _make_offer(INIT_ID, 600), _make_offer(PARTNER_ID),
        [_item(PARTNER_ID)], [INIT_ID, PARTNER_ID], status=DealStatus.DRAFT,
    )
    with pytest.raises(DealNotReadyError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_not_ready_when_partner_empty():
    """У партнёра пустое предложение → ошибка"""
    use_case, _ = _build(
        _make_offer(INIT_ID), _make_offer(PARTNER_ID),
        [_item(INIT_ID)], [INIT_ID, PARTNER_ID],
    )
    with pytest.raises(DealNotReadyError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_self_weight_limit():
    """Мне некуда принять товары → моя ошибка веса"""
    balances = {
        INIT_ID: type('B', (), {'weight': 90, 'max_weight': 100})(),
        PARTNER_ID: type('B', (), {'weight': 0, 'max_weight': 100})(),
    }
    use_case, _ = _build(
        _make_offer(INIT_ID, 600), _make_offer(PARTNER_ID),
        [_item(PARTNER_ID)], [INIT_ID, PARTNER_ID],
        balances=balances, incoming={INIT_ID: 20},
    )
    with pytest.raises(DealSelfWeightLimitError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_partner_weight_limit():
    """Партнёру некуда принять товары → ошибка веса партнёра"""
    balances = {
        INIT_ID: type('B', (), {'weight': 0, 'max_weight': 100})(),
        PARTNER_ID: type('B', (), {'weight': 90, 'max_weight': 100})(),
    }
    use_case, _ = _build(
        _make_offer(INIT_ID), _make_offer(PARTNER_ID, 600),
        [_item(INIT_ID)], [INIT_ID, PARTNER_ID],
        balances=balances, incoming={PARTNER_ID: 20},
    )
    with pytest.raises(DealPartnerWeightLimitError):
        await use_case(uuid.uuid4(), USER)


@pytest.mark.asyncio
async def test_confirm_success_sets_confirmation():
    """Успешное подтверждение: моя ревизия зафиксирована, партнёр ещё нет"""
    my_offer = _make_offer(INIT_ID)
    partner_offer = _make_offer(PARTNER_ID, 600)
    use_case, deal = _build(my_offer, partner_offer, [_item(INIT_ID)], [INIT_ID, PARTNER_ID])

    await use_case(uuid.uuid4(), USER)

    assert my_offer.confirmed_revision == my_offer.revision
    assert deal.initiator_confirmed_at is not None
    assert partner_offer.confirmed_revision is None