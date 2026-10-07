"""Юнит-тесты AcceptDealUseCase: принятие DRAFT-сделки партнёром (DRAFT -> ACTIVE)."""
import uuid
from types import SimpleNamespace

import pytest

from shared.schemas.deal_events import DealEventType

from mining_app.apps.items.deals.enums import DealStatus
from mining_app.apps.items.deals.exceptions import (
    DealAccessDeniedError,
    DealNotFoundError,
    DealProximityError,
    DealStateError,
)
from mining_app.apps.items.deals.use_cases import AcceptDealUseCase

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeSession,
    make_deal,
    make_user,
)


def _build(deal, online_ids=(INIT_ID, PARTNER_ID)):
    async def get_for_participant(deal_id, character_id, for_update=None):
        return deal

    repository = SimpleNamespace(session=FakeSession(), get_for_participant=get_for_participant)
    client = FakeCharacterClient(online_ids)
    events = FakeEvents()
    return AcceptDealUseCase(repository, client, events), events


@pytest.mark.asyncio
async def test_accept_draft_to_active():
    """Партнёр принимает DRAFT-сделку: статус ACTIVE, время жизни обновлено, событие отправлено."""
    deal = make_deal(status=DealStatus.DRAFT)
    old_expires_at = deal.expires_at
    use_case, events = _build(deal)

    result = await use_case(uuid.uuid4(), make_user(PARTNER_ID))

    assert deal.status == DealStatus.ACTIVE
    assert deal.expires_at > old_expires_at
    assert result.status == DealStatus.ACTIVE
    assert events.published[-1].event_type == DealEventType.ACCEPTED


@pytest.mark.asyncio
async def test_accept_by_initiator_forbidden():
    """Принять может только партнёр — инициатор получает DealAccessDeniedError."""
    deal = make_deal(status=DealStatus.DRAFT)
    use_case, _ = _build(deal)

    with pytest.raises(DealAccessDeniedError):
        await use_case(uuid.uuid4(), make_user(INIT_ID))


@pytest.mark.asyncio
async def test_accept_already_active_raises_state_error():
    """Повторное принятие ACTIVE-сделки запрещено."""
    deal = make_deal(status=DealStatus.ACTIVE)
    use_case, _ = _build(deal)

    with pytest.raises(DealStateError):
        await use_case(uuid.uuid4(), make_user(PARTNER_ID))


@pytest.mark.asyncio
async def test_accept_when_partner_offline_raises_proximity():
    """Партнёр оффлайн (нет в списке онлайн в локации) — принять нельзя."""
    deal = make_deal(status=DealStatus.DRAFT)
    use_case, _ = _build(deal, online_ids=[INIT_ID])

    with pytest.raises(DealProximityError):
        await use_case(uuid.uuid4(), make_user(PARTNER_ID))


@pytest.mark.asyncio
async def test_accept_unknown_deal_raises_not_found():
    """Сделка не найдена / пользователь не участник."""
    use_case, _ = _build(None)

    with pytest.raises(DealNotFoundError):
        await use_case(uuid.uuid4(), make_user(PARTNER_ID))
