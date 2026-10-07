"""Сброс подтверждений при изменении оффера (SetDealDucatsUseCase -> _touch_offer).

Сценарий: инициатор подтвердил сделку, партнёр меняет свой оффер —
подтверждение должно сброситься у ОБОИХ сторон (иначе партнёр мог бы
«передумать» после подтверждения контрагента незаметно для него).
"""
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from shared.schemas.deal_events import DealEventType

from mining_app.apps.items.deals.enums import DealLedgerOperationKind, DealLedgerOperationStatus
from mining_app.apps.items.deals.exceptions import DealInsufficientFundsError
from mining_app.apps.items.deals.models import DealLedgerOperation
from mining_app.apps.items.deals.use_cases import SetDealDucatsUseCase

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeLedgerRepo,
    FakeSession,
    make_deal,
    make_offer,
    make_user,
)


def _build(deal, init_offer, partner_offer, *, client_ducats=Decimal("10000"), my_items=None):
    init_offer.deal_id = deal.id
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_for_character(deal_id, cid, for_update=None):
        return partner_offer  # пользователь в этих тестах — партнёр

    async def get_by_deal(deal_id, for_update=None):
        return [init_offer, partner_offer]

    async def items_by_deal(deal_id):
        return my_items or []

    repository = SimpleNamespace(session=FakeSession(), get_for_participant=get_for_participant)
    offer_repo = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_by_deal=items_by_deal)
    ledger = FakeLedgerRepo()
    client = FakeCharacterClient([INIT_ID, PARTNER_ID], ducats=client_ducats)
    events = FakeEvents()
    use_case = SetDealDucatsUseCase(repository, offer_repo, item_repo, ledger, client, events)
    return use_case, client, ledger, events, repository


@pytest.mark.asyncio
async def test_partner_change_after_confirm_resets_both_confirmations():
    """Партнёр меняет оффер после подтверждения инициатором — подтверждения сброшены у обоих."""
    deal = make_deal()
    init_offer = make_offer(INIT_ID, confirmed=1)   # инициатор уже подтвердил
    partner_offer = make_offer(PARTNER_ID)
    use_case, client, ledger, events, repository = _build(deal, init_offer, partner_offer)

    data = SimpleNamespace(operation_id=uuid.uuid4(), amount=Decimal("500"))
    result = await use_case(deal.id, make_user(PARTNER_ID), data)

    # подтверждения сброшены у обеих сторон
    assert init_offer.confirmed_revision is None
    assert partner_offer.confirmed_revision is None
    # оффер партнёра обновлён, ревизия выросла
    assert partner_offer.revision == 2
    assert partner_offer.ducats_escrowed == Decimal("500")
    assert result.ducats_escrowed == Decimal("500")
    # эскроу-списание проведено и зафиксировано в ledger (через session.add)
    assert client.debits == [(PARTNER_ID, Decimal("500"), data.operation_id)]
    ledger_ops = [obj for obj in repository.session.added if isinstance(obj, DealLedgerOperation)]
    assert len(ledger_ops) == 1
    assert ledger_ops[0].operation_kind == DealLedgerOperationKind.ESCROW_HOLD
    assert ledger_ops[0].status == DealLedgerOperationStatus.APPLIED
    assert ledger_ops[0].character_id == PARTNER_ID
    assert events.published[-1].event_type == DealEventType.UPDATED


@pytest.mark.asyncio
async def test_set_ducats_insufficient_funds_leaves_offer_untouched():
    """Недостаточно дукатов: ошибка, оффер не изменён, списаний и ledger-записей нет."""
    deal = make_deal()
    init_offer = make_offer(INIT_ID, confirmed=1)
    partner_offer = make_offer(PARTNER_ID)
    use_case, client, ledger, _, repository = _build(deal, init_offer, partner_offer, client_ducats=Decimal("100"))

    data = SimpleNamespace(operation_id=uuid.uuid4(), amount=Decimal("500"))
    with pytest.raises(DealInsufficientFundsError):
        await use_case(deal.id, make_user(PARTNER_ID), data)

    assert partner_offer.ducats_escrowed == Decimal("0")
    assert partner_offer.revision == 1
    assert client.debits == []
    assert repository.session.added == []
