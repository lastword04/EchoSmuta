"""Фейк-объекты для юнит-тестов сделок (без БД).

Используются всеми тестами пакета tests/deals. Паттерн повторяет
существующие тесты (tests/test_confirm_deal.py и др.): моки доменных
объектов через SimpleNamespace, фейковые репозитории с async-замыканиями.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mining_app.apps.items.deals.enums import DealAssetType, DealStatus  # noqa: E402

INIT_ID = uuid.uuid4()
PARTNER_ID = uuid.uuid4()
LOCATION = "1.13.forge"


class _Ctx:
    """Имитация async with session.begin()."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Result:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return self._rows


class FakeSession:
    """Фейк AsyncSession: фиксирует add/delete/execute; scalar/get — из очередей."""

    def __init__(self, rows=None, scalars=None, gets=None):
        self.rows = rows or []
        self._scalars = list(scalars or [])
        self._gets = dict(gets or {})
        self.added = []
        self.deleted = []
        self.executed = 0

    def begin(self):
        return _Ctx()

    def add(self, obj):
        if getattr(obj, "id", None) is None and hasattr(obj, "id"):
            obj.id = uuid.uuid4()
        self.added.append(obj)

    def add_all(self, objs):
        for obj in objs:
            self.add(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        pass

    async def execute(self, *a, **k):
        self.executed += 1
        return _Result(self.rows)

    async def scalar(self, *a, **k):
        return self._scalars.pop(0) if self._scalars else None

    async def get(self, model, ident, with_for_update=None):
        return self._gets.get(ident)


class FakeCharacterClient:
    """Фейк клиента characters-сервиса; фиксирует debits/credits."""

    def __init__(self, online_ids, ducats=Decimal("10000"), balances=None,
                 partner_location=LOCATION, gold_trade_enabled=True):
        self.online_ids = set(online_ids)
        self.ducats = ducats
        self.balances = balances or {}
        self.partner_location = partner_location
        self.gold_trade_enabled = gold_trade_enabled
        self.debits = []   # (character_id, amount, operation_id)
        self.credits = []  # (character_id, amount, operation_id)

    async def get_online_characters(self, location_slug):
        return SimpleNamespace(objects=[SimpleNamespace(id=cid) for cid in self.online_ids])

    async def get_full_character(self, cid):
        return SimpleNamespace(location_slug=self.partner_location, gold=Decimal("0"))

    async def get_character_weight_balance(self, cid):
        return self.balances.get(cid, SimpleNamespace(weight=0, max_weight=100))

    async def get_simple_character_balance(self, cid):
        return SimpleNamespace(ducats=self.ducats, gold=Decimal("0"))

    async def get_trade_privileges(self, cid):
        return SimpleNamespace(gold_trade_enabled=self.gold_trade_enabled)

    async def debit_ducats(self, cid, amount, operation_id, *a, **k):
        self.debits.append((cid, Decimal(str(amount)), operation_id))

    async def credit_ducats(self, cid, amount, operation_id, *a, **k):
        self.credits.append((cid, Decimal(str(amount)), operation_id))

    async def credit_gold(self, cid, amount, operation_id, *a, **k):
        self.credits.append((cid, Decimal(str(amount)), operation_id))

    async def debit_gold(self, cid, amount, operation_id, *a, **k):
        self.debits.append((cid, Decimal(str(amount)), operation_id))


class FakeEvents:
    def __init__(self):
        self.published = []

    async def publish_deal_event(self, schema):
        self.published.append(schema)


class FakeLedgerRepo:
    def __init__(self, by_operation_id=None):
        self.by_operation_id = dict(by_operation_id or {})
        self.created = []

    async def get_by_operation_id(self, operation_id):
        return self.by_operation_id.get(operation_id)

    async def create_many(self, ops):
        self.created.extend(ops)


class FakeReservationRepo:
    def __init__(self, reserved=0, active=None):
        self.reserved = reserved
        self.active = active
        self.released = []

    async def reserved_amount(self, cid, slug):
        return self.reserved

    async def get_active_for_item(self, item_id, for_update=None):
        return self.active

    async def release_active_for_deal(self, deal_id):
        self.released.append(deal_id)


def make_deal(status=DealStatus.ACTIVE):
    """Сделка со всеми полями DealReadSchema (нужны для model_validate)."""
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        status=status,
        initiator_character_id=INIT_ID,
        partner_character_id=PARTNER_ID,
        location_slug=LOCATION,
        expires_at=now + timedelta(minutes=30),
        cancelled_by_character_id=None,
        cancelled_at=None,
        created_at=now,
        updated_at=now,
        completed_at=None,
        initiator_confirmed_at=None,
        partner_confirmed_at=None,
    )


def make_offer(cid, ducats=0, gold=0, revision=1, confirmed=None):
    """Оффер со всеми полями DealOfferReadSchema (deal_id проставляет билдер)."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        deal_id=None,
        character_id=cid,
        ducats_amount=Decimal(str(ducats)),
        ducats_escrowed=Decimal(str(ducats)),
        gold_amount=Decimal(str(gold)),
        gold_escrowed=Decimal(str(gold)),
        revision=revision,
        confirmed_revision=confirmed,
    )


def make_deal_item(owner_cid, offer_id, *, asset_type=DealAssetType.INVENTORY_ITEM,
                   resource_slug=None, inventory_item_id=None, amount=1, snapshot=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        deal_id=None,
        offer_id=offer_id,
        owner_character_id=owner_cid,
        asset_type=asset_type,
        resource_slug=resource_slug,
        inventory_item_id=inventory_item_id,
        amount=amount,
        item_snapshot=snapshot if snapshot is not None else {},
    )


def make_user(cid):
    return SimpleNamespace(character_id=cid)
