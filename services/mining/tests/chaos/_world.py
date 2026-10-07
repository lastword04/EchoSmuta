"""In-memory «живой мир» для хаос-тестирования сделок.

Симулирует реальный геймплей на уровне USE CASES без внешних сервисов:

* персонажи с балансами (дукаты/золото), локацией, онлайн-статусом,
  весом, лицензиями, экипировкой, инвентарём и ресурсами;
* сделки/офферы/деал-айтэмы/резервации/ledger в оперативной памяти;
* транзакции через ``session.begin()`` с откатом (snapshot на входе,
  restore при исключении) — как у настоящего БД-тора;
* ``session.get/scalar/execute`` интерпретирует ОГРАНИЧЕННОЕ число
  SQLAlchemy-запросов, которые реально генерируют use cases сделок;
* character-клиент идемпотентен по operation_id (как characters-сервис);
* ``world/now`` — единые часы: тесты экспирации подменяют
  ``deals.datetime`` через ``ClockPatch`` без time.sleep.

Домен (НАМЕРЕННО НЕ МЕНЯЕТСЯ):
  - «отменить сделку» == снять СВОЁ предложение (деал остаётся живой,
    статус не меняется, expires_at продлевается);
  - ключ cancel-refund включает ревизию оффера: новый operation_id
    на каждый цикл эскроу;
  - у одной стороны либо деньги, либо товары (DealMixedOfferError);
  - деньги с двух сторон / товары с двух сторон запрещены.
"""

import asyncio
import copy
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import sqlalchemy as sa

from mining_app.apps.items.deals.enums import (
    DealAssetType,
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)
from mining_app.apps.items.deals.exceptions import (
    DealAccessDeniedError,
    DealNotReadyError,
    DealStateError,
)
from mining_app.apps.items.deals.use_cases import (
    AcceptDealUseCase,
    AddDealInventoryItemUseCase,
    AddDealResourceUseCase,
    CancelDealUseCase,
    CancelDealsForCharacterUseCase,
    CompleteDealUseCase,
    ConfirmDealUseCase,
    CreateDealUseCase,
    ExpireDealUseCase,
    GetDealUseCase,
    ListDealsUseCase,
    RemoveDealItemUseCase,
    SetDealDucatsUseCase,
    SetDealGoldUseCase,
)
from mining_app.apps.items.deals.schemas import (
    DealCreateSchema,
    DealCurrencyOfferUpdateSchema,
    DealInventoryItemOfferCreateSchema,
    DealResourceOfferUpdateSchema,
)
from mining_app.apps.items.deals.schemas import DealReadSchema  # noqa: F401  (re-export for tests)
from mining_app.apps.items.enums import ItemBindingType
from mining_app.apps.items.models import InventoryItem, Item
from mining_app.apps.resources.models import CharacterResource, Resource

DEAL_LOC = "1.13.forge"
DEAL_LIFETIME = timedelta(minutes=30)
DUCATS_START = Decimal("30000")
GOLD_START = Decimal("0")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dec(v) -> Decimal:
    return Decimal(str(v))


# ==========================================================================
# СУЩНОСТИ МИРА
# ==========================================================================

def make_character(cid, name="Боец", location=DEAL_LOC, *, ducats=DUCATS_START,
                   gold=GOLD_START, weight=0, max_weight=500):
    return SimpleNamespace(
        _entity="character",
        id=cid, name=name, level=10, race="human",
        location_slug=location, online=True,
        ducats=_dec(ducats), gold=_dec(gold),
        weight=weight, max_weight=max_weight,
        eff_power=0, eff_agility=0, eff_lucky=0,
    )


def make_inventory(cid, slug, amount=1, *, deal_id=None, shop_id=None,
                   binding=ItemBindingType.NONE):
    return SimpleNamespace(
        _entity="inventory",
        id=uuid.uuid4(), character_id=cid, shop_id=shop_id, deal_id=deal_id,
        item_slug=slug, amount=amount, expired_date=None, used_count=None,
        wear=0, item_binding_type=binding,
    )


def make_item_spec(slug, name, price, *, weight=10, item_type="weapon",
                   location=DEAL_LOC, stackable=False, can_sell=True):
    return SimpleNamespace(
        _entity="item", slug=slug, name=name, item_type=item_type,
        location_slug=location, price=_dec(price), weight=weight,
        minimal_level=0, race=None, parameters={}, ability_parameters={},
        is_stackable=stackable, can_sell=can_sell,
    )


def make_resource_spec(slug, name, price, *, weight=2):
    return SimpleNamespace(
        _entity="res", slug=slug, name=name, price=_dec(price), weight=weight,
    )


def make_character_resource(cid, slug, amount):
    return SimpleNamespace(
        _entity="charres", character_id=cid, resource_slug=slug, amount=amount,
    )
def make_deal_entity(init_id, partner_id, loc=DEAL_LOC, status=DealStatus.DRAFT, now=None):
    now = now or _now()
    return SimpleNamespace(
        _entity="deal",
        id=uuid.uuid4(),
        status=status,
        initiator_character_id=init_id,
        partner_character_id=partner_id,
        location_slug=loc,
        initiator_confirmed_at=None,
        partner_confirmed_at=None,
        completed_at=None,
        cancelled_at=None,
        cancelled_by_character_id=None,
        expires_at=now + DEAL_LIFETIME,
        created_at=now,
        updated_at=now,
    )


def make_offer_entity(deal, cid, *, revision=0):
    return SimpleNamespace(
        _entity="offer",
        id=uuid.uuid4(),
        deal_id=deal.id,
        character_id=cid,
        ducats_amount=Decimal("0"),
        ducats_escrowed=Decimal("0"),
        gold_amount=Decimal("0"),
        gold_escrowed=Decimal("0"),
        revision=revision,
        confirmed_revision=None,
    )


def make_deal_item_entity(deal, offer, owner_cid, *, asset_type=DealAssetType.INVENTORY_ITEM,
                          resource_slug=None, inventory_item_id=None, amount=1, snapshot=None):
    return SimpleNamespace(
        _entity="item",
        id=uuid.uuid4(),
        deal_id=deal.id,
        offer_id=offer.id,
        owner_character_id=owner_cid,
        asset_type=asset_type,
        resource_slug=resource_slug,
        inventory_item_id=inventory_item_id,
        amount=amount,
        item_snapshot=snapshot if snapshot is not None else {},
    )


def make_reservation_entity(deal, deal_item, cid, slug, amount,
                            status=ResourceReservationStatus.ACTIVE):
    return SimpleNamespace(
        _entity="reservation",
        id=uuid.uuid4(), deal_id=deal.id, deal_item_id=deal_item.id,
        character_id=cid, resource_slug=slug, amount=amount, status=status,
    )


def make_ledger_entity(deal, operation_id, kind, cid, counterparty_id, currency,
                       amount, status, payload=None):
    return SimpleNamespace(
        _entity="ledger",
        id=uuid.uuid4(), deal_id=deal.id, operation_id=operation_id,
        operation_kind=kind, character_id=cid, counterparty_id=counterparty_id,
        currency=currency, amount=_dec(amount), status=status, payload=payload,
    )


def make_license(cid, end_date=None):
    return SimpleNamespace(
        _entity="license", character_id=cid,
        end_date=end_date if end_date is not None else _now() + timedelta(days=30),
    )


# ==========================================================================
# STORE — единое mutable-хранилище мира (deepcopy-снимок на транзакцию)
# ==========================================================================

class Store:
    def __init__(self):
        self.deals = {}          # deal_id -> deal
        self.offers = {}         # (deal_id, character_id) -> offer
        self.items = {}          # deal_item_id -> deal item
        self.reservations = {}   # deal_item_id -> reservation
        self.ledger = {}         # operation_id -> ledger op
        self.ledger_list = []    # все op (в т.ч. дубликаты — для детекта гонок)
        self.licenses = {}       # character_id -> license
        self.inventory = {}      # inventory_item_id -> inventory item
        self.equipped = set()    # inventory ids (надето)
        self.for_sale = set()    # inventory ids (на продаже)
        self.resources = {}      # (character_id, slug) -> charres
        self.characters = {}     # character_id -> character
        self.item_catalog = {}   # slug -> item spec
        self.resource_catalog = {}  # slug -> res spec
        self.events = []         # (DealEventType, deal_id, details)
        self.calls = []          # лог HTTP-вызовов клиента characters
        self.processed_op_ids = set()  # идемпотентность characters-операций
# ==========================================================================
# FAKE SESSION — транзакции, add/get/delete, разбор ограниченного набора SQL
# ==========================================================================

class _Rows:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return self._rows


class _TxCtx:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        await self.session._lock.acquire()
        self.session._snapshot = copy.deepcopy(self.session.store)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is not None:
                self.session.store = self.session._snapshot
            return False
        finally:
            self.session._lock.release()


class FakeDealSession:
    """Сессия-адаптер: begin() с откатом, примитивный разбор SELECT/UPDATE."""

    def __init__(self, store):
        self.store = store
        self._lock = asyncio.Lock()
        self._snapshot = None

    # ── время ──
    def now(self):
        # Единый источник времени: через модуль deals, который тесты могут
        # подменить ClockPatch (без time.sleep) для сценария экспирации.
        from mining_app.apps.items.deals.use_cases import deal_operations as _d
        return _d.datetime.now(timezone.utc)

    def begin(self):
        return _TxCtx(self)

    # ── DML ──
    def add(self, obj):
        if obj is None:
            return
        store = self.store
        e = getattr(obj, "_entity", None)
        if e == "deal" or (e is None and hasattr(obj, "initiator_character_id")
                           and hasattr(obj, "partner_character_id") and hasattr(obj, "status")):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = self.now()
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = self.now()
            if getattr(obj, "expires_at", None) is None:
                obj.expires_at = obj.updated_at + DEAL_LIFETIME
            store.deals[obj.id] = obj
            return
        if e == "offer" or (e is None and hasattr(obj, "deal_id") and hasattr(obj, "character_id")
                            and hasattr(obj, "ducats_escrowed") and not hasattr(obj, "item_snapshot")):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            if getattr(obj, "ducats_amount", None) is None:
                obj.ducats_amount = Decimal("0")
            if getattr(obj, "ducats_escrowed", None) is None:
                obj.ducats_escrowed = Decimal("0")
            if getattr(obj, "gold_amount", None) is None:
                obj.gold_amount = Decimal("0")
            if getattr(obj, "gold_escrowed", None) is None:
                obj.gold_escrowed = Decimal("0")
            if getattr(obj, "revision", None) is None:
                obj.revision = 0
            if not hasattr(obj, "confirmed_revision"):
                obj.confirmed_revision = None
            store.offers[(obj.deal_id, obj.character_id)] = obj
            return
        if e == "item" or (e is None and hasattr(obj, "offer_id") and hasattr(obj, "owner_character_id")
                           and hasattr(obj, "asset_type")):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            store.items[obj.id] = obj
            return
        if e == "reservation" or (e is None and hasattr(obj, "deal_item_id")
                                  and hasattr(obj, "resource_slug") and hasattr(obj, "status")):
            store.reservations[obj.deal_item_id] = obj
            return
        if e == "ledger" or (e is None and hasattr(obj, "operation_id")
                             and hasattr(obj, "currency") and hasattr(obj, "operation_kind")):
            store.ledger[obj.operation_id] = obj
            store.ledger_list.append(obj)
            return
        if e == "inventory" or (e is None and hasattr(obj, "item_slug")
                                and hasattr(obj, "deal_id") and hasattr(obj, "character_id")
                                and not hasattr(obj, "name")):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            store.inventory[obj.id] = obj
            return
        if e == "charres" or (e is None and hasattr(obj, "resource_slug")
                              and hasattr(obj, "character_id") and hasattr(obj, "amount")
                              and not hasattr(obj, "operation_id")):
            store.resources[(obj.character_id, obj.resource_slug)] = obj
            return

    def add_all(self, objs):
        for o in objs:
            self.add(o)

    async def flush(self):
        pass

    async def delete(self, obj):
        store = self.store
        e = getattr(obj, "_entity", None)
        if e == "item" or (e is None and hasattr(obj, "offer_id")
                           and hasattr(obj, "owner_character_id")):
            store.items.pop(obj.id, None)
            return
        if e == "reservation":
            store.reservations.pop(obj.deal_item_id, None)
            return
        if e == "offer" or (e is None and hasattr(obj, "ducats_escrowed")):
            store.offers.pop((obj.deal_id, obj.character_id), None)
            return
        if e == "inventory" or (e is None and hasattr(obj, "item_slug") and hasattr(obj, "deal_id")):
            store.inventory.pop(obj.id, None)
            return

    # ── get ──
    async def get(self, model, ident, with_for_update=None):
        if getattr(model, "__name__", None) == "InventoryItem":
            return self.store.inventory.get(ident)
        return None
# ── SQL-эмуляция ──
    async def execute(self, stmt):
        if isinstance(stmt, sa.sql.dml.Update):
            self._apply_update(stmt)
            return _Rows([])
        return _Rows(self._select_rows(stmt))

    async def scalar(self, stmt):
        return self._select_scalar(stmt)

    # ── Внутренности ──

    def _wheres(self, stmt):
        """Возвращает список BinaryExpression из where-критериев."""
        out = []

        def walk(ex):
            if isinstance(ex, sa.sql.elements.ClauseList):
                for c in ex.clauses:
                    walk(c)
            elif isinstance(ex, (sa.sql.expression.BinaryExpression,)):
                out.append(ex)

        for crit in getattr(stmt, "_where_criteria", ()):
            walk(crit)
        return out

    def _value_of(self, binary):
        return getattr(binary.right, "value", binary.right)

    def _select_rows(self, stmt):
        entity = self._entity_of(stmt)
        store = self.store
        name = getattr(entity, "__name__", None)
        if name == "Item":
            return [(spec.slug, spec.price) for spec in store.item_catalog.values()]
        if name == "Resource":
            return [(spec.slug, spec.price) for spec in store.resource_catalog.values()]
        return []

    def _select_scalar(self, stmt):
        entity = self._entity_of(stmt)
        store = self.store
        name = getattr(entity, "__name__", None)
        if name == "CharacterResource":
            cid = None
            slug = None
            for b in self._wheres(stmt):
                col = getattr(b.left, "name", None)
                if col == "character_id":
                    cid = self._value_of(b)
                elif col == "resource_slug":
                    slug = self._value_of(b)
            if cid is not None and slug is not None:
                return store.resources.get((cid, slug))
            return None
        if name == "Resource":
            slug = None
            for b in self._wheres(stmt):
                if getattr(b.left, "name", None) == "slug":
                    slug = self._value_of(b)
            return store.resource_catalog.get(slug)
        return None

    def _entity_of(self, stmt):
        descs = stmt.column_descriptions
        if not descs:
            return None
        return descs[0].get("entity")

    def _apply_update(self, stmt):
        """sa.update(DealLedgerOperation)... → помечает op статусом APPLIED."""
        store = self.store
        target_name = getattr(getattr(stmt, "table", None), "name", "")
        if target_name != "deal_ledger_operations":
            return
        op_ids = []
        for b in self._wheres(stmt):
            if getattr(b.left, "name", None) == "operation_id" \
                    and b.operator is sa.sql.operators.in_op:
                op_ids = list(self._value_of(b))
        if not op_ids:
            return
        for op_id in op_ids:
            op = store.ledger.get(op_id)
            if op is not None:
                op.status = DealLedgerOperationStatus.APPLIED


# ==========================================================================
# CHARACTER CLIENT — идемпотентные debit/credit как в characters-сервисе
# ==========================================================================

class WorldClient:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    # ── чтение ──
    async def get_online_characters(self, location_slug):
        objects = [
            SimpleNamespace(id=cid)
            for cid, c in self.store.characters.items()
            if c.online and c.location_slug == location_slug
        ]
        return SimpleNamespace(objects=objects)

    async def get_full_character(self, cid):
        c = self.store.characters[cid]
        return SimpleNamespace(name=c.name, level=c.level,
                               location_slug=c.location_slug, gold=c.gold)

    async def get_character_weight_balance(self, cid):
        c = self.store.characters[cid]
        return SimpleNamespace(weight=c.weight, max_weight=c.max_weight)

    async def get_simple_character_balance(self, cid):
        c = self.store.characters[cid]
        return SimpleNamespace(ducats=c.ducats, gold=c.gold)

    async def get_simple_info_character(self, cid):
        c = self.store.characters[cid]
        return SimpleNamespace(name=c.name, level=c.level)

    async def get_trade_privileges(self, cid):
        return SimpleNamespace(gold_trade_enabled=True)

    # ── операции с валютами (идемпотентны по operation_id) ──
    async def debit_ducats(self, cid, amount, operation_id, *a, **k):
        self._change(cid, "ducats", -amount, operation_id)

    async def debit_gold(self, cid, amount, operation_id, *a, **k):
        self._change(cid, "gold", -amount, operation_id)

    async def credit_ducats(self, cid, amount, operation_id, *a, **k):
        self._change(cid, "ducats", amount, operation_id)

    async def credit_gold(self, cid, amount, operation_id, *a, **k):
        self._change(cid, "gold", amount, operation_id)

    def _change(self, cid, currency, delta, operation_id):
        self.store.calls.append((f"{currency}:{'credit' if delta >= 0 else 'debit'}",
                                 cid, operation_id, delta))
        if operation_id in self.store.processed_op_ids:
            return  # characters-сервис не проводит одну операцию дважды
        self.store.processed_op_ids.add(operation_id)
        ch = self.store.characters[cid]
        setattr(ch, currency, getattr(ch, currency) + _dec(delta))
# ==========================================================================
# IN-MEMORY РЕПОЗИТОРИИ (зеркалят SQLAlchemy-репозитории сделок)
# ==========================================================================

class InMemoryDealRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    def _bump(self, deal):
        deal.updated_at = self.session.now()

    def _get(self, deal_id, *, for_update=False):
        deal = self.store.deals.get(deal_id)
        if deal is not None and for_update:
            self._bump(deal)
        return deal

    async def get_for_update(self, deal_id):
        return self._get(deal_id, for_update=True)

    async def get_for_participant(self, deal_id, character_id, for_update=False):
        deal = self.store.deals.get(deal_id)
        if deal is None:
            return None
        if deal.initiator_character_id != character_id and deal.partner_character_id != character_id:
            return None
        if for_update:
            self._bump(deal)
        return deal

    async def get_detail_for_participant(self, deal_id, character_id):
        deal = await self.get_for_participant(deal_id, character_id)
        if deal is None:
            return None
        offers = [o for (did, _cid), o in self.store.offers.items() if did == deal.id]
        items = [it for it in self.store.items.values() if it.deal_id == deal.id]
        return deal, offers, items

    async def list_for_participant(self, character_id, statuses, limit, offset):
        deals = [
            d for d in self.store.deals.values()
            if d.initiator_character_id == character_id or d.partner_character_id == character_id
        ]
        if statuses:
            wanted = set(statuses)
            deals = [d for d in deals if d.status in wanted]
        deals.sort(key=lambda d: d.updated_at, reverse=True)
        return deals[offset:offset + limit], len(deals)

    async def list_expired_for_update(self, now, limit):
        deals = [
            d for d in self.store.deals.values()
            if d.status in (DealStatus.DRAFT, DealStatus.ACTIVE) and d.expires_at <= now
        ]
        deals.sort(key=lambda d: d.expires_at)
        return deals[:limit]

    async def list_completing(self, limit):
        deals = [d for d in self.store.deals.values() if d.status == DealStatus.COMPLETING]
        deals.sort(key=lambda d: d.updated_at)
        return deals[:limit]

    async def list_completing_for_update(self, limit):
        return await self.list_completing(limit)

    async def list_active_for_character(self, character_id):
        return [
            d for d in self.store.deals.values()
            if d.status in (DealStatus.DRAFT, DealStatus.ACTIVE)
            and (d.initiator_character_id == character_id or d.partner_character_id == character_id)
        ]


class InMemoryDealOfferRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def get_by_deal(self, deal_id, for_update=False):
        return [o for (did, _cid), o in self.store.offers.items() if did == deal_id]

    async def get_for_character(self, deal_id, character_id, for_update=False):
        return self.store.offers.get((deal_id, character_id))
class InMemoryDealItemRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def get_by_deal(self, deal_id, for_update=False):
        return [it for it in self.store.items.values() if it.deal_id == deal_id]

    async def clear_inventory_deal_id(self, deal_id):
        for inv in self.store.inventory.values():
            if inv.deal_id == deal_id:
                inv.deal_id = None

    async def get_for_offer_asset(self, offer_id, asset_type, resource_slug=None, for_update=False):
        for it in self.store.items.values():
            if it.offer_id == offer_id and it.asset_type == asset_type \
                    and it.resource_slug == resource_slug:
                return it
        return None

    async def get_for_deal_item(self, deal_id, deal_item_id, for_update=False):
        item = self.store.items.get(deal_item_id)
        if item is None or item.deal_id != deal_id:
            return None
        return item

    async def get_inventory_for_trade(self, inventory_item_id, for_update=False):
        inv = self.store.inventory.get(inventory_item_id)
        if inv is None:
            return None
        item = self.store.item_catalog.get(inv.item_slug)
        equipped = inventory_item_id in self.store.equipped
        for_sale = inventory_item_id in self.store.for_sale
        return inv, item, equipped, for_sale

    async def incoming_weight(self, deal_id, recipient_id):
        deal = self.store.deals.get(deal_id)
        if deal is None:
            return 0
        owner_id = (deal.partner_character_id if recipient_id == deal.initiator_character_id
                    else deal.initiator_character_id)
        total = 0
        for it in self.store.items.values():
            if it.deal_id != deal_id or it.owner_character_id != owner_id:
                continue
            if it.asset_type == DealAssetType.INVENTORY_ITEM and it.inventory_item_id:
                inv = self.store.inventory.get(it.inventory_item_id)
                if inv:
                    spec = self.store.item_catalog.get(inv.item_slug)
                    total += it.amount * (spec.weight if spec else 10)
            elif it.asset_type == DealAssetType.RESOURCE and it.resource_slug:
                rspec = self.store.resource_catalog.get(it.resource_slug)
                total += it.amount * (rspec.weight if rspec else 2)
        return total

    async def transfer_assets(self, deal, items):
        store = self.store
        for item in items:
            recipient_id = (deal.partner_character_id
                            if item.owner_character_id == deal.initiator_character_id
                            else deal.initiator_character_id)
            if item.asset_type == DealAssetType.INVENTORY_ITEM:
                inv = store.inventory.get(item.inventory_item_id)
                if inv is None or inv.deal_id != deal.id:
                    raise ValueError("Deal inventory item is no longer locked")
                inv.character_id = recipient_id
                inv.deal_id = None
            else:
                key = (item.owner_character_id, item.resource_slug)
                src = store.resources.get(key)
                if src is None or src.amount < item.amount:
                    raise ValueError("Reserved resource is no longer available")
                src.amount -= item.amount
                tgt_key = (recipient_id, item.resource_slug)
                tgt = store.resources.get(tgt_key)
                if tgt is None:
                    store.resources[tgt_key] = make_character_resource(
                        recipient_id, item.resource_slug, item.amount)
                else:
                    tgt.amount += item.amount
class InMemoryResourceReservationRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def release_active_for_deal(self, deal_id):
        for r in self.store.reservations.values():
            if r.deal_id == deal_id and r.status == ResourceReservationStatus.ACTIVE:
                r.status = ResourceReservationStatus.RELEASED

    async def get_active_for_item(self, deal_item_id, for_update=False):
        r = self.store.reservations.get(deal_item_id)
        if r is None or r.status != ResourceReservationStatus.ACTIVE:
            return None
        return r

    async def reserved_amount(self, character_id, resource_slug):
        return sum(r.amount for r in self.store.reservations.values()
                   if r.character_id == character_id and r.resource_slug == resource_slug
                   and r.status == ResourceReservationStatus.ACTIVE)

    async def mark_transferred_for_deal(self, deal_id):
        for r in self.store.reservations.values():
            if r.deal_id == deal_id and r.status == ResourceReservationStatus.ACTIVE:
                r.status = ResourceReservationStatus.TRANSFERRED


class InMemoryLedgerRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def get_by_operation_id(self, operation_id):
        return self.store.ledger.get(operation_id)

    async def create_many(self, ops):
        for op in ops:
            self.store.ledger[op.operation_id] = op
            self.store.ledger_list.append(op)


class InMemoryTradeLicenseRepository:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def get_for_character(self, character_id, for_update=False):
        return self.store.licenses.get(character_id)


class InMemoryDealEvents:
    def __init__(self, session):
        self.session = session

    @property
    def store(self):
        return self.session.store

    async def publish_deal_event(self, event):
        self.store.events.append((event.event_type, event.deal_id, event.details))
# ==========================================================================
# WORLD — сборка мира и use cases + «игровые» действия игрока
# ==========================================================================

class World:
    def __init__(self):
        self.session = FakeDealSession(Store())
        self.client = WorldClient(self.session)
        self.ucs = self._build_ucs()

    # ── use cases (паттерн как в tests/integration/conftest.py) ──
    def _build_ucs(self):
        session = self.session
        repo = InMemoryDealRepository(session)
        offer_repo = InMemoryDealOfferRepository(session)
        item_repo = InMemoryDealItemRepository(session)
        res_repo = InMemoryResourceReservationRepository(session)
        ledger = InMemoryLedgerRepository(session)
        lic = InMemoryTradeLicenseRepository(session)
        events = InMemoryDealEvents(session)
        client = self.client

        self.repo = repo
        self.offer_repo = offer_repo
        self.item_repo = item_repo
        self.res_repo = res_repo
        self.ledger = ledger
        self.events = events
        self.licenses = lic

        complete = CompleteDealUseCase(
            repo, offer_repo, item_repo, res_repo, ledger, lic,
            client, deal_tax=0.10, discounted_tax=0.03, deal_events=events,
        )
        confirm = ConfirmDealUseCase(repo, offer_repo, item_repo, complete, client, deal_events=events)
        self.complete_uc = complete
        self.confirm_uc = confirm
        self.create_uc = CreateDealUseCase(repo, offer_repo, client, deal_events=events)
        self.accept_uc = AcceptDealUseCase(repo, client, deal_events=events)
        self.cancel_uc = CancelDealUseCase(
            repo, offer_repo, item_repo, res_repo, ledger,
            deal_events=events, character_client=client,
        )
        self.cancel_for_character_uc = CancelDealsForCharacterUseCase(repo, self.cancel_uc)
        self.set_ducats_uc = SetDealDucatsUseCase(
            repo, offer_repo, item_repo, ledger, client, deal_events=events,
        )
        self.set_gold_uc = SetDealGoldUseCase(
            repo, offer_repo, item_repo, ledger, client, deal_events=events,
        )
        self.add_item_uc = AddDealInventoryItemUseCase(
            repo, offer_repo, item_repo, client, deal_events=events,
        )
        self.remove_item_uc = RemoveDealItemUseCase(
            repo, offer_repo, item_repo, res_repo, client, deal_events=events,
        )
        self.add_res_uc = AddDealResourceUseCase(
            repo, offer_repo, item_repo, res_repo, client, deal_events=events,
        )
        self.expire_uc = ExpireDealUseCase(
            repo, offer_repo, item_repo, res_repo, ledger, client, deal_events=events,
        )
        self.get_uc = GetDealUseCase(repo, offer_repo, item_repo)
        self.list_uc = ListDealsUseCase(repo)
        return SimpleNamespace(
            create=self.create_uc, accept=self.accept_uc, cancel=self.cancel_uc,
            cancel_for_character=self.cancel_for_character_uc,
            set_ducats=self.set_ducats_uc, set_gold=self.set_gold_uc,
            add_item=self.add_item_uc, remove_item=self.remove_item_uc,
            add_res=self.add_res_uc, confirm=self.confirm_uc, complete=complete,
            expire=self.expire_uc, get=self.get_uc, list=self.list_uc,
        )
# ── доступ к store ──
    @property
    def store(self):
        return self.session.store

    def character(self, cid):
        return self.store.characters[cid]

    def inventory(self, inv_id):
        return self.store.inventory[inv_id]

    def offer(self, deal_id, cid):
        return self.store.offers.get((deal_id, cid))

    # ── настройка мира ──
    def add_character(self, cid, name="Боец", *, ducats=DUCATS_START, location=DEAL_LOC, **kw):
        ch = make_character(cid, name, location, ducats=ducats, **kw)
        self.store.characters[cid] = ch
        return ch

    def add_item_spec(self, slug, name, price, **kw):
        self.store.item_catalog[slug] = make_item_spec(slug, name, price, **kw)

    def add_resource_spec(self, slug, name, price, **kw):
        self.store.resource_catalog[slug] = make_resource_spec(slug, name, price, **kw)

    def give_item(self, cid, slug, amount=1, *, deal_id=None, shop_id=None):
        inv = make_inventory(cid, slug, amount, deal_id=deal_id, shop_id=shop_id)
        self.store.inventory[inv.id] = inv
        return inv

    def give_resource(self, cid, slug, amount):
        self.store.resources[(cid, slug)] = make_character_resource(cid, slug, amount)

    def grant_license(self, cid, end_date=None):
        self.store.licenses[cid] = make_license(cid, end_date)

    def move_character(self, cid, location, online=True):
        ch = self.store.characters[cid]
        ch.location_slug = location
        ch.online = online

    # ── «игровые» действия игрока (не часть домена сделок) ──
    def equip(self, cid, inv_id):
        inv = self.store.inventory.get(inv_id)
        if inv is None or inv.character_id != cid:
            return
        self.store.equipped.add(inv_id)

    def unequip(self, cid, inv_id):
        self.store.equipped.discard(inv_id)

    def count_free_items(self, cid):
        return sum(1 for inv in self.store.inventory.values()
                   if inv.character_id == cid and inv.deal_id is None
                   and inv.id not in self.store.equipped)
# ==========================================================================
# CLOCK PATCH — виртуальные часы для сценария экспирации (без time.sleep)
# ==========================================================================

class _FakeDatetime:
    """Класс-подмена datetime в модуле deals.use_cases (без freezegun)."""

    _current = None

    @staticmethod
    def now(tz=None):
        if _FakeDatetime._current is not None:
            return _FakeDatetime._current
        return datetime.now(tz)


class ClockPatch:
    """Контекстный менеджер: подменяет ``datetime`` в модуле use_cases.

    Пример::

        with ClockPatch(world, advance=timedelta(minutes=31)):
            expired = await world.ucs.expire()
    """

    def __init__(self, world, now=None, advance=None):
        from mining_app.apps.items.deals.use_cases.deal_operations import (
            accept_deal,
            cancel_deal,
            create_deal,
            expire_deal,
        )
        self._modules = [expire_deal, create_deal, accept_deal, cancel_deal]
        if now is not None:
            self._target = now
        elif advance is not None:
            self._target = expire_deal.datetime.now(timezone.utc) + advance
        else:
            raise ValueError("ClockPatch: задайте now или advance")

    def __enter__(self):
        _FakeDatetime._current = self._target
        self._orig_datetimes = {mod: mod.datetime for mod in self._modules}
        for mod in self._modules:
            mod.datetime = _FakeDatetime
        return self

    def __exit__(self, *exc):
        for mod, orig in self._orig_datetimes.items():
            mod.datetime = orig
        _FakeDatetime._current = None
        return False


# ==========================================================================
# БЫСТРЫЕ ХЕЛПЕРЫ ДЛЯ ТЕСТОВ
# ==========================================================================

def make_user(cid):
    return SimpleNamespace(character_id=cid)


async def set_ducats(world, deal_id, cid, amount, operation_id=None):
    """Выставить дукаты в сделке (новая операция эскроу по умолчанию)."""
    return await world.ucs.set_ducats(
        deal_id, make_user(cid),
        DealCurrencyOfferUpdateSchema(
            amount=_dec(amount),
            operation_id=operation_id or uuid.uuid4(),
        ),
    )


async def set_gold(world, deal_id, cid, amount, operation_id=None):
    """Выставить золото в сделке (новая операция эскроу по умолчанию)."""
    return await world.ucs.set_gold(
        deal_id, make_user(cid),
        DealCurrencyOfferUpdateSchema(
            amount=_dec(amount),
            operation_id=operation_id or uuid.uuid4(),
        ),
    )


async def add_item(world, deal_id, cid, inv_id, amount=1):
    return await world.ucs.add_item(
        deal_id, make_user(cid),
        DealInventoryItemOfferCreateSchema(inventory_item_id=inv_id, amount=amount),
    )


async def add_resource(world, deal_id, cid, resource_slug, amount):
    """Добавить ресурс в сделку."""
    return await world.ucs.add_res(
        deal_id, resource_slug, make_user(cid),
        DealResourceOfferUpdateSchema(amount=amount),
    )


async def remove_item(world, deal_id, cid, deal_item_id):
    return await world.ucs.remove_item(deal_id, deal_item_id, make_user(cid))


async def create_deal(world, init_id, partner_id, loc=DEAL_LOC):
    return await world.ucs.create(make_user(init_id), DealCreateSchema(
        partner_character_id=partner_id, location_slug=loc))


def item_specs(world):
    return world.store.item_catalog


def default_world(*, items=(("s1", "Меч", 400), ("s2", "Топор", 350), ("s3", "Шлем", 300)),
                  money=DUCATS_START):
    """Мир в локации '1.13.forge' с A (инициатор) и B (партнёр)."""
    import uuid as _uuid
    A = _uuid.uuid4()
    B = _uuid.uuid4()
    world = World()
    world.add_character(A, "Алекс", ducats=money)
    world.add_character(B, "Бо", ducats=money)
    for slug, name, price in items:
        world.add_item_spec(slug, name, price)
    world.add_resource_spec("iron", "Железо", 100)
    world.add_resource_spec("wood", "Древесина", 50)
    return world, A, B