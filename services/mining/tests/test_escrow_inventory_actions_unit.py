"""Юнит-тесты эскроу-проверок unpack_kit и use_consumable.

Сценарий: предмет в сделке (inventory_items.deal_id != NULL) «заморожен» —
его нельзя распаковать или использовать, иначе операция удалит предмет,
а CompleteDealUseCase.transfer_assets упадёт (500). Equip уже защищён;
здесь проверяем UnpackKitUseCase и UseConsumableUseCase (по образцу
test_equip_use_case.py: моки зависимостей через unittest.mock).
"""

import os
import sys
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from mining_app.apps.items.enums import ItemType  # noqa: E402
from mining_app.apps.items.use_cases.items.unpack_kit import (  # noqa: E402
    UnpackKitUseCase,
)
from mining_app.apps.items.use_cases.items.use_consumable import (  # noqa: E402
    UseConsumableUseCase,
)
from mining_app.core.utils.exceptions import ValidationError  # noqa: E402

# ===================== UNPACK KIT =====================


def _make_unpack_use_case(inventory_item) -> "tuple[UnpackKitUseCase, MagicMock]":
    inventory_service = MagicMock()
    inventory_service.get_by_id_and_character = AsyncMock(return_value=inventory_item)
    inventory_service.consume_item = AsyncMock()
    inventory_service.add_item = AsyncMock(
        return_value=SimpleNamespace(id=uuid.uuid4())
    )

    use_case = UnpackKitUseCase(inventory_service=inventory_service)
    return use_case, inventory_service


def _kit_inventory_item(*, deal_id=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        deal_id=deal_id,
        item=SimpleNamespace(
            item_type=ItemType.KIT,
            parameters={"kit_items": ["i.arm.1.1.part-a", "i.arm.1.1.part-b"]},
        ),
    )


@pytest.mark.asyncio
async def test_unpack_kit_blocked_when_in_deal():
    """Комплект в сделке распаковать нельзя: ValidationError, consume_item не вызывается."""
    use_case, inventory_service = _make_unpack_use_case(
        inventory_item=_kit_inventory_item(deal_id=uuid.uuid4())
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert "в сделке" in exc_info.value.message
    inventory_service.consume_item.assert_not_awaited()
    inventory_service.add_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_unpack_kit_normal_kit_passes():
    """Обычный комплект (deal_id=None) распаковывается: consume + add_item по составу."""
    use_case, inventory_service = _make_unpack_use_case(
        inventory_item=_kit_inventory_item(deal_id=None)
    )

    created = await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    inventory_service.consume_item.assert_awaited_once()
    assert len(created) == 2
    inventory_service.add_item.assert_awaited()


@pytest.mark.asyncio
async def test_unpack_kit_not_in_inventory_raises_validation_error():
    """Предмет не найден в инвентаре: get_by_id_and_character возвращает None →
    ValidationError (а не AttributeError → 500)."""
    use_case, inventory_service = _make_unpack_use_case(inventory_item=None)

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert exc_info.value.field == "inventory_item_id"
    assert "не найден" in exc_info.value.message
    inventory_service.consume_item.assert_not_awaited()
    inventory_service.add_item.assert_not_awaited()


# ===================== USE CONSUMABLE =====================


def _make_consumable_use_case(inventory_item) -> "tuple[UseConsumableUseCase, MagicMock]":
    inventory_service = MagicMock()
    inventory_service.get_by_id_and_character = AsyncMock(return_value=inventory_item)
    inventory_service.consume_item = AsyncMock()

    characters_client = MagicMock()
    characters_client.get_character_for_requirements = AsyncMock(
        return_value=SimpleNamespace(level=10, race=None, eff_power=100, eff_agility=100, eff_lucky=100)
    )
    characters_client.apply_buff = AsyncMock()
    # используется при публикации системного сообщения (обёрнуто в try/except, но мок нужен для await)
    characters_client.get_simple_info_character = AsyncMock(
        return_value=SimpleNamespace(location_slug="1.13.forge")
    )

    # --- items_events / template_service (обязательные зависимости конструктора) ---
    items_events = MagicMock()
    items_events.publish_message = AsyncMock()

    template_service = MagicMock()
    template_service.get_consumable_use_message = MagicMock(return_value="Использован предмет")

    use_case = UseConsumableUseCase(
        inventory_service=inventory_service,
        characters_client=characters_client,
        items_events=items_events,
        template_service=template_service,
    )
    return use_case, inventory_service, characters_client


def _consumable_inventory_item(*, deal_id=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        deal_id=deal_id,
        item=SimpleNamespace(
            name="Алхимическое зелье силы",
            item_type=ItemType.ELIXIR,
            ability_parameters={"power_number": 3},
            parameters={},
        ),
    )


@pytest.mark.asyncio
async def test_use_consumable_blocked_when_in_deal():
    """Предмет в сделке использовать нельзя: ValidationError, consume/apply_buff не вызываются."""
    use_case, inventory_service, characters_client = _make_consumable_use_case(
        inventory_item=_consumable_inventory_item(deal_id=uuid.uuid4())
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert "в сделке" in exc_info.value.message
    inventory_service.consume_item.assert_not_awaited()
    characters_client.apply_buff.assert_not_awaited()


@pytest.mark.asyncio
async def test_use_consumable_normal_passes():
    """Обычный эликсир (deal_id=None) применяется: apply_buff + consume_item."""
    use_case, inventory_service, characters_client = _make_consumable_use_case(
        inventory_item=_consumable_inventory_item(deal_id=None)
    )

    await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    characters_client.apply_buff.assert_awaited()
    inventory_service.consume_item.assert_awaited_once()


@pytest.mark.asyncio
async def test_use_consumable_not_in_inventory_raises_validation_error():
    """Предмет не найден в инвентаре: get_by_id_and_character возвращает None →
    ValidationError (а не AttributeError → 500)."""
    use_case, inventory_service, characters_client = _make_consumable_use_case(
        inventory_item=None
    )

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert exc_info.value.field == "inventory_item_id"
    assert "не найден" in exc_info.value.message
    inventory_service.consume_item.assert_not_awaited()
    characters_client.apply_buff.assert_not_awaited()
