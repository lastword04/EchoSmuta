"""Хаос-сценарий 6: смешанные предложения и ошибки валидации.

Проверяет корректную обработку невалидных состояний:
  - Деньги + предмет в одном оффере -> DealMixedOfferError.
  - Предмет + деньги в одном оффере -> DealMixedOfferError.
  - Оба кладут предметы -> DealBothSidesGoodsError.
  - Оба кладут деньги -> DealBothSidesMoneyError.
"""

from decimal import Decimal

import pytest

from mining_app.apps.items.deals.enums import DealStatus
from mining_app.apps.items.deals.exceptions import (
    DealBothSidesGoodsError,
    DealBothSidesMoneyError,
    DealMixedOfferError,
)

from tests.chaos._world import (
    add_item,
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


async def test_money_then_item_raises_mixed_offer():
    """B кладёт деньги и пытается положить предмет -> DealMixedOfferError."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    # B кладёт деньги
    await set_ducats(world, deal.id, B, Decimal("500"))
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("500")

    # B пытается положить предмет -> DealMixedOfferError
    sword = world.give_item(B, "s1")
    with pytest.raises(DealMixedOfferError) as exc:
        await add_item(world, deal.id, B, sword.id)
    assert exc.value.error_code == "DEAL_MIXED_OFFER"

    # Состояние не изменилось
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("500")
    assert world.inventory(sword.id).deal_id is None


async def test_item_then_money_raises_mixed_offer():
    """B кладёт предмет и пытается положить деньги -> DealMixedOfferError."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    # B кладёт предмет
    sword = world.give_item(B, "s1")
    await add_item(world, deal.id, B, sword.id)
    assert world.inventory(sword.id).deal_id == deal.id

    # B пытается положить деньги -> DealMixedOfferError
    with pytest.raises(DealMixedOfferError) as exc:
        await set_ducats(world, deal.id, B, Decimal("300"))
    assert exc.value.error_code == "DEAL_MIXED_OFFER"

    # Состояние не изменилось
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")
    assert world.inventory(sword.id).deal_id == deal.id


async def test_both_sides_goods_raises():
    """A кладёт предмет и B кладёт предмет -> DealBothSidesGoodsError."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    # A кладёт предмет
    sword_a = world.give_item(A, "s1")
    await add_item(world, deal.id, A, sword_a.id)

    # B пытается положить предмет -> DealBothSidesGoodsError
    sword_b = world.give_item(B, "s2")
    with pytest.raises(DealBothSidesGoodsError) as exc:
        await add_item(world, deal.id, B, sword_b.id)
    assert exc.value.error_code == "DEAL_BOTH_SIDES_GOODS"

    # Предмет B не попал в сделку
    assert world.inventory(sword_b.id).deal_id is None


async def test_both_sides_money_raises():
    """A кладёт деньги и B кладёт деньги -> DealBothSidesMoneyError."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    # A кладёт деньги
    await set_ducats(world, deal.id, A, Decimal("500"))

    # B пытается положить деньги -> DealBothSidesMoneyError
    with pytest.raises(DealBothSidesMoneyError) as exc:
        await set_ducats(world, deal.id, B, Decimal("300"))
    assert exc.value.error_code == "DEAL_BOTH_SIDES_MONEY"

    # Деньги B не попали в сделку
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")