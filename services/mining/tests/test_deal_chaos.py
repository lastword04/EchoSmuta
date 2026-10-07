import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from hypothesis import settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from shared.exceptions import CoreException

from mining_app.apps.items.deals.use_cases import (
    AcceptDealUseCase,
    SetDealDucatsUseCase,
    AddDealInventoryItemUseCase,
    RemoveDealItemUseCase,
    CancelDealUseCase,
    ConfirmDealUseCase,
)
from mining_app.apps.items.deals.enums import DealStatus, DealAssetType, TRADEABLE_ITEM_TYPES
from mining_app.apps.items.enums import ItemBindingType

A, B = uuid.uuid4(), uuid.uuid4()
L = '1.13.forge'
PRICES = {'sword': Decimal('1000')}
ITEM_TYPE = next(iter(TRADEABLE_ITEM_TYPES))


class World:
    def __init__(self):
        self.deal = None
        self.offers = {}
        self.items = []
        self.online = {A, B}
        self.loc = {A: L, B: L}
        self.ducats = {A: Decimal('10000'), B: Decimal('10000')}
        self.backpack = {}
        self.completed = False


class _Ctx:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Result:
    def __init__(s, rows): s._rows = list(rows.items())
    def all(s): return s._rows


class FakeSession:
    def __init__(s, w): s.w = w
    def begin(s): return _Ctx()
    def flush(s): pass
    def add_all(s, objs): pass
    async def execute(s, *a, **k): return _Result(PRICES)
    def add(s, obj):
        if getattr(obj, 'id', None) is None: obj.id = uuid.uuid4()
        if hasattr(obj, 'asset_type') and hasattr(obj, 'offer_id'):
            s.w.items.append(obj)
    def delete(s, obj):
        if obj in s.w.items: s.w.items.remove(obj)
    async def get(s, cls, id, with_for_update=None):
        return s.w.backpack.get(id)


class FakeClient:
    def __init__(s, w): s.w = w
    async def get_online_characters(s, slug):
        return type('R', (), {'objects': [type('C', (), {'id': i})() for i in s.w.online]})()
    async def get_full_character(s, cid):
        return type('FC', (), {'location_slug': s.w.loc[cid]})()
    async def get_character_weight_balance(s, cid):
        return type('B', (), {'weight': 0, 'max_weight': 100})()
    async def get_simple_character_balance(s, cid):
        return type('B', (), {'ducats': s.w.ducats[cid], 'gold': Decimal('0')})()
    async def get_trade_privileges(s, cid):
        return type('P', (), {'gold_trade_enabled': True})()
    async def debit_ducats(s, cid, amt, *a, **k): s.w.ducats[cid] -= Decimal(str(amt))
    async def credit_ducats(s, cid, amt, *a, **k): s.w.ducats[cid] += Decimal(str(amt))


class FakeLedger:
    async def get_by_operation_id(s, *a, **k): return None
    async def create_many(s, *a, **k): pass


class FakeReserv:
    async def get_active_for_item(s, *a, **k): return None
    async def reserved_amount(s, *a, **k): return 0


class FakeEvents:
    async def publish_deal_event(self, *a, **k): return None


async def _aw(v):
    return v


def _offer(cid):
    return type('O', (), {'character_id': cid, 'ducats_amount': Decimal('0'),
        'ducats_escrowed': Decimal('0'), 'gold_amount': Decimal('0'), 'gold_escrowed': Decimal('0'),
        'revision': 1, 'confirmed_revision': None})()


def _u(cid):
    return type('U', (), {'character_id': cid})()


def money(o):
    return o.ducats_escrowed + o.gold_escrowed * Decimal('70')


def goods(w, cid):
    return sum((i.amount * PRICES.get(i.item_snapshot.get('item_slug'), Decimal('0')) for i in w.items if i.owner_character_id == cid), Decimal('0'))


class DealChaos(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.w = World()
        s = FakeSession(self.w)
        client = FakeClient(self.w)
        self.client = client
        fake_events = FakeEvents()
        
        repo = type('R', (), {'session': s,
            'get_for_participant': lambda *a, **k: _aw(self.w.deal),
            'get_for_update': lambda *a, **k: _aw(self.w.deal)})()
        offer_repo = type('OR', (), {
            'get_for_character': lambda *a, **k: _aw(self.w.offers.get(a[1] if len(a) > 1 else a[0])),
            'get_by_deal': lambda *a, **k: _aw(list(self.w.offers.values()))})()
        item_repo = type('IR', (), {
            'get_by_deal': lambda *a, **k: _aw(self.w.items),
            'get_for_deal_item': lambda *a, **k: _aw(next((i for i in self.w.items if i.id == a[-1]), None)),
            'get_for_offer_asset': lambda *a, **k: _aw(next((i for i in self.w.items if i.offer_id == a[0]), None)),
            'get_inventory_for_trade': lambda *a, **k: _aw(self._inv(a[0])),
            'incoming_weight': lambda *a, **k: _aw(0)})()
        item_repo._inv = lambda id: (self.w.backpack.get(id), self._item(), False, False) if self.w.backpack.get(id) else None
        item_repo._item = lambda: type('I', (), {'slug': 'sword', 'name': 'Sword', 'item_type': ITEM_TYPE,
            'location_slug': L, 'can_sell': True, 'is_stackable': False})()

        self.accept = AcceptDealUseCase(repo, client, fake_events)
        self.set_duc = SetDealDucatsUseCase(repo, offer_repo, item_repo, FakeLedger(), client, fake_events)
        self.add_item = AddDealInventoryItemUseCase(repo, offer_repo, item_repo, client, fake_events)
        self.rem_item = RemoveDealItemUseCase(repo, offer_repo, item_repo, FakeReserv(), client, fake_events)
        self.cancel = CancelDealUseCase(repo, offer_repo, item_repo, FakeReserv(), FakeLedger(), fake_events, client)
        self.confirm = ConfirmDealUseCase(repo, offer_repo, item_repo, self._complete, client, fake_events)

    async def _complete(self, deal_id):
        self.w.completed = True
        return None

    @initialize()
    def setup(self):
        now = datetime.now(timezone.utc)
        d = type('D', (), {'id': uuid.uuid4(), 'status': DealStatus.DRAFT,
            'initiator_character_id': A, 'partner_character_id': B, 'location_slug': L,
            'expires_at': now + timedelta(minutes=30),
            'cancelled_by_character_id': None, 'cancelled_at': None,
            'created_at': now, 'updated_at': now, 'completed_at': None,
            'initiator_confirmed_at': None, 'partner_confirmed_at': None})()
        self.w.deal = d
        self.w.offers = {A: _offer(A), B: _offer(B)}
        for cid in (A, B):
            inv = type('V', (), {'id': uuid.uuid4(), 'character_id': cid, 'item_slug': 'sword',
                'amount': 1, 'deal_id': None, 'shop_id': None, 'expired_date': None,
                'used_count': None, 'wear': None, 'item_binding_type': ItemBindingType.NONE})()
            self.w.backpack[inv.id] = inv

    @rule()
    def accept(self): self._run(self.accept(self.w.deal.id, _u(B)))

    @rule()
    def add_money_a(self): self._add_money(A)
    @rule()
    def add_money_b(self): self._add_money(B)
    @rule()
    def remove_money_a(self): self._set_money(A, 0)

    @rule()
    def add_item_a(self): self._add_item(A)
    @rule()
    def add_item_b(self): self._add_item(B)
    @rule()
    def remove_item_a(self): self._remove_item(A)

    @rule()
    def cancel_a(self): self._run(self.cancel(self.w.deal.id, A))
    @rule()
    def cancel_b(self): self._run(self.cancel(self.w.deal.id, B))

    @rule()
    def confirm_a(self): self._run(self.confirm(self.w.deal.id, _u(A)))
    @rule()
    def confirm_b(self): self._run(self.confirm(self.w.deal.id, _u(B)))

    @rule()
    def leave_b(self): self.w.online.discard(B); self.w.loc[B] = '9.99.other'
    @rule()
    def return_b(self): self.w.online.add(B); self.w.loc[B] = L
    @rule()
    def reload(self): pass

    @invariant()
    def no_both_money(self):
        o = self.w.offers
        assert not (money(o[A]) > 0 and money(o[B]) > 0)

    @invariant()
    def no_both_goods(self):
        assert not (goods(self.w, A) > 0 and goods(self.w, B) > 0)

    @invariant()
    def no_mixed(self):
        for cid in (A, B):
            assert not (money(self.w.offers[cid]) > 0 and goods(self.w, cid) > 0)

    def _run(self, coro):
        try:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()
        except CoreException:
            pass

    def _add_money(self, cid):
        cur = self.w.offers[cid].ducats_escrowed
        self._set_money(cid, cur + 100)

    def _set_money(self, cid, amount):
        data = type('D', (), {'operation_id': uuid.uuid4(), 'amount': Decimal(str(amount))})()
        self._run(self.set_duc(self.w.deal.id, _u(cid), data))

    def _add_item(self, cid):
        inv = next((v for v in self.w.backpack.values() if v.character_id == cid and v.deal_id is None), None)
        if not inv: return
        data = type('D', (), {'inventory_item_id': inv.id, 'amount': inv.amount})()
        self._run(self.add_item(self.w.deal.id, _u(cid), data))

    def _remove_item(self, cid):
        it = next((i for i in self.w.items if i.owner_character_id == cid), None)
        if not it: return
        self._run(self.rem_item(self.w.deal.id, it.id, _u(cid)))


TestChaos = DealChaos.TestCase
TestChaos.settings = settings(max_examples=30, stateful_step_count=12,
                              suppress_health_check=[HealthCheck.too_slow])