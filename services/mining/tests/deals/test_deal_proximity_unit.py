"""Юнит-тесты: нарушения проксимити при создании/принятии сделки.

Покрывают два сценария из чек-листа:
1) CreateDealUseCase: партнёр не в той же локации (оффлайн) → DealProximityError;
2) AcceptDealUseCase: инициатор уже ушёл из локации → DealProximityError.
"""
import uuid
from types import SimpleNamespace

import pytest

from mining_app.apps.items.deals.enums import DealStatus
from mining_app.apps.items.deals.exceptions import DealProximityError
from mining_app.apps.items.deals.use_cases import AcceptDealUseCase, CreateDealUseCase

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    LOCATION,
    FakeCharacterClient,
    FakeEvents,
    FakeSession,
    make_deal,
    make_user,
)


@pytest.mark.asyncio
async def test_create_deal_with_offline_partner_raises():
    """Инициатор создаёт сделку, партнёр не в локации (оффлайн) → DealProximityError."""
    client = FakeCharacterClient([INIT_ID])  # в онлайне только инициатор
    events = FakeEvents()
    repository = SimpleNamespace(session=FakeSession())
    offer_repository = SimpleNamespace()
    use_case = CreateDealUseCase(repository, offer_repository, client, events)

    data = SimpleNamespace(partner_character_id=PARTNER_ID, location_slug=LOCATION)

    with pytest.raises(DealProximityError):
        await use_case(make_user(INIT_ID), data)

    # Сделка не создана (ничего не добавлено в сессию), событие не отправлено
    assert repository.session.added == []
    assert events.published == []


@pytest.mark.asyncio
async def test_create_deal_partner_in_other_location_raises():
    """Партнёр онлайн, но в другой локации → DealProximityError."""
    # FakeCharacterClient.get_online_characters возвращает только персонажей
    # указанных в online_ids для КОНКРЕТНОЙ локации; инициатор и партнёр в
    # разных локациях = партнёр отсутствует в списке локации инициатора.
    client = FakeCharacterClient([PARTNER_ID])  # в локации только партнёр
    events = FakeEvents()
    repository = SimpleNamespace(session=FakeSession())
    use_case = CreateDealUseCase(repository, SimpleNamespace(), client, events)

    data = SimpleNamespace(partner_character_id=PARTNER_ID, location_slug=LOCATION)

    with pytest.raises(DealProximityError):
        await use_case(make_user(INIT_ID), data)


@pytest.mark.asyncio
async def test_accept_deal_when_initiator_left_raises():
    """Партнёр принимает сделку, но инициатор уже ушёл из локации → DealProximityError."""
    deal = make_deal(status=DealStatus.DRAFT)
    client = FakeCharacterClient([PARTNER_ID])  # в локации только партнёр

    async def get_for_participant(deal_id, character_id, for_update=None):
        return deal

    repository = SimpleNamespace(session=FakeSession(), get_for_participant=get_for_participant)
    events = FakeEvents()
    use_case = AcceptDealUseCase(repository, client, events)

    with pytest.raises(DealProximityError):
        await use_case(uuid.uuid4(), make_user(PARTNER_ID))

    # Сделка не принята (осталась DRAFT), событие не отправлено
    assert deal.status == DealStatus.DRAFT
    assert events.published == []