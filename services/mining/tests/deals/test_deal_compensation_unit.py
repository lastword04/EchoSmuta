"""Юнит-тест CompleteDealUseCase: компенсация выплат при сбое передачи активов.

Сценарий (из CompleteDealUseCase.__call__):
- Фаза 1 (HTTP): credit_ducats/credit_gold получателям → payouts.
- Фаза 2 (транзакция): transfer_assets(...) падает.
- Компенсация: для каждой выплаты (в обратном порядке) вызывается
  debit_ducats/debit_gold с compensation_id (идемпотентный operation_id).
"""
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mining_app.apps.items.deals.enums import DealStatus
from mining_app.apps.items.deals.use_cases import CompleteDealUseCase, _operation_id

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeLedgerRepo,
    FakeReservationRepo,
    FakeSession,
    make_deal,
    make_deal_item,
    make_offer,
)

DEAL_TAX = 0.10
DISCOUNTED_TAX = 0.03


def _build(deal, init_offer, partner_offer, items):
    init_offer.deal_id = deal.id
    partner_offer.deal_id = deal.id
    # Цены предметов для _goods_prices (session.execute -> список строк)
    price_rows = [("sword", Decimal("1000"))]

    async def get_for_update(deal_id):
        return deal

    async def get_by_deal(deal_id, for_update=None):
        return [init_offer, partner_offer]

    async def items_by_deal(deal_id, for_update=None):
        return items

    async def incoming_weight(deal_id, cid):
        return 0

    async def transfer_assets(deal, items):
        # Фаза 2 падает: эмуляция сбоя передачи предметов
        raise RuntimeError("asset transfer failed (simulated)")

    async def inventory_for_trade(item_id, for_update=None):
        # Equipped-проверка (escrow): предмет в сделке НЕ надет -> проверка проходит,
        # и флоу доходит до transfer_assets, который эмулирует сбой.
        return SimpleNamespace(), SimpleNamespace(), False, False

    async def license_for(cid):
        return None  # лицензии нет -> обычный налог

    repository = SimpleNamespace(
        session=FakeSession(rows=price_rows),
        get_for_update=get_for_update,
    )
    offer_repository = SimpleNamespace(get_by_deal=get_by_deal)
    item_repository = SimpleNamespace(
        get_by_deal=items_by_deal,
        incoming_weight=incoming_weight,
        transfer_assets=transfer_assets,
        get_inventory_for_trade=inventory_for_trade,
    )
    license_repository = SimpleNamespace(get_for_character=license_for)
    client = FakeCharacterClient([INIT_ID, PARTNER_ID])
    events = FakeEvents()

    use_case = CompleteDealUseCase(
        repository,
        offer_repository,
        item_repository,
        FakeReservationRepo(),
        FakeLedgerRepo(),
        license_repository,
        client,
        DEAL_TAX,
        DISCOUNTED_TAX,
        events,
    )
    return use_case, client, deal


@pytest.mark.asyncio
async def test_complete_compensates_payouts_when_asset_transfer_fails():
    """Фаза 1 прошла (credit_*), Фаза 2 упала -> debit_* для каждой выплаты в обратном порядке."""
    deal = make_deal()
    init_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600, gold=100)
    # Оба оффера подтверждены (требование готовности к завершению)
    init_offer.confirmed_revision = init_offer.revision
    partner_offer.confirmed_revision = partner_offer.revision

    items = [make_deal_item(INIT_ID, init_offer.id, snapshot={"item_slug": "sword"})]
    use_case, client, deal = _build(deal, init_offer, partner_offer, items)

    with pytest.raises(RuntimeError):
        await use_case(deal.id)

    # --- Фаза 1: выплаты получателю (инициатор получает деньги партнёра) ---
    # ducats: 600 - 10% = 540; gold: 100 - 10% = 90
    payout_ducats_id = _operation_id(deal.id, f"{INIT_ID}:DUCATS:income")
    payout_gold_id = _operation_id(deal.id, f"{INIT_ID}:GOLD:income")
    assert client.credits == [
        (INIT_ID, Decimal("540"), payout_ducats_id),
        (INIT_ID, Decimal("90"), payout_gold_id),
    ]

    # --- Компенсация: debit в ОБРАТНОМ порядке (gold -> ducats) ---
    comp_gold_id = _operation_id(deal.id, f"{payout_gold_id}:compensation")
    comp_ducats_id = _operation_id(deal.id, f"{payout_ducats_id}:compensation")
    assert client.debits == [
        (INIT_ID, Decimal("90"), comp_gold_id),
        (INIT_ID, Decimal("540"), comp_ducats_id),
    ]

    # Итоги: сделка остановлена в COMPLETING, компенсационные operation_id детерминированные
    assert deal.status == DealStatus.COMPLETING
    assert comp_ducats_id != payout_ducats_id