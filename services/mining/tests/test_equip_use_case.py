"""Юнит-тесты для EquipItemUseCase (эскроу сделок + регресс на 500).

Контекст: EquipItemUseCase читает ``inventory_item.deal_id`` для блокировки
надевания предметов, находящихся в сделке. Раньше ``get_by_id_and_character``
возвращал ``InventoryItemReadSchema``, у которого поля ``deal_id`` не было —
pydantic молча отбрасывал ключ из ``__dict__`` ORM-объекта (extra='ignore'),
и обращение к атрибуту кидало AttributeError → 500 на ЛЮБОЙ предмет.

Покрывают:

* ``test_read_schema_exposes_deal_id`` — схема принимает deal_id и отдаёт атрибут
  (именно так её строят репозитории: ``InventoryItemReadSchema(**item_dict, item=...)``);
* ``test_equip_normal_item_not_in_deal_passes`` — обычный предмет (deal_id=None)
  проходит проверку и доходит до ``EquipmentService.equip`` (регресс на 500);
* ``test_equip_item_in_deal_blocked`` — предмет в сделке (deal_id задан)
  блокируется ValidationError, service.equip не вызывается.

Все зависимости конструктора мокаются через ``unittest.mock``:
``AsyncMock`` — для awaitable-методов, ``MagicMock`` — для самих объектов.
"""

import os
import sys
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# --- путь до корня сервиса mining, чтобы импортировать mining_app (как в test_sale_items.py) ---
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from mining_app.apps.items.enums import ItemType  # noqa: E402
from mining_app.apps.items.schemas import (  # noqa: E402
    InventoryItemReadSchema,
    ItemReadSchema,
)
from mining_app.apps.items.use_cases.items.equip import EquipItemUseCase  # noqa: E402
from mining_app.core.utils.exceptions import ValidationError  # noqa: E402


def _make_item_schema() -> ItemReadSchema:
    """Справочник предмета без требований к статам/расе."""
    return ItemReadSchema(
        id=uuid.uuid4(),
        name="Тестовый шлем",
        slug="test.helmet",
        item_type=ItemType.HELMET,
        location_slug="1.13.forge",
        price=Decimal("15.00"),
        weight=10,
        minimal_level=0,
        is_stackable=False,
        can_sell=True,
        race=None,
        parameters={},
        ability_parameters={},
    )


def _make_inventory_item(deal_id: uuid.UUID | None) -> InventoryItemReadSchema:
    """Инвентарная строка, как её возвращает CharacterItemRepository.get_by_id_and_character
    (те же kwargs, что и в репозитории: **item_dict + item)."""
    return InventoryItemReadSchema(
        id=uuid.uuid4(),
        character_id=uuid.uuid4(),
        shop_id=None,
        item_slug="test.helmet",
        amount=1,
        expired_date=None,
        used_count=None,
        wear=0,
        deal_id=deal_id,
        item=_make_item_schema(),
    )


def _make_use_case(inventory_item: InventoryItemReadSchema):
    """Собирает EquipItemUseCase с моками зависимостей и возвращает (use_case, service_mock)."""
    service = MagicMock()
    service.equip = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))

    inventory_service = MagicMock()
    inventory_service.get_by_id_and_character = AsyncMock(return_value=inventory_item)

    characters_client = MagicMock()
    characters_client.get_character_for_requirements = AsyncMock(
        return_value=SimpleNamespace(level=10, race="human", eff_power=100, eff_agility=100, eff_lucky=100)
    )

    use_case = EquipItemUseCase(
        service=service,
        inventory_service=inventory_service,
        characters_client=characters_client,
    )
    return use_case, service


# ===================== ТЕСТЫ =====================

@pytest.mark.asyncio
async def test_read_schema_exposes_deal_id():
    """Схема обязана хранить deal_id: репозитории передают его через **item_dict из __dict__."""
    deal_id = uuid.uuid4()
    inventory_item = _make_inventory_item(deal_id=deal_id)
    assert inventory_item.deal_id == deal_id

    # None-вариант (предмет не в сделке) — атрибут существует и равен None
    assert _make_inventory_item(deal_id=None).deal_id is None


@pytest.mark.asyncio
async def test_equip_normal_item_not_in_deal_passes():
    """Регресс на 500: обычный предмет (deal_id=None) экипируется без AttributeError."""
    use_case, service = _make_use_case(inventory_item=_make_inventory_item(deal_id=None))

    result = await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert result is service.equip.return_value
    service.equip.assert_awaited_once()


@pytest.mark.asyncio
async def test_equip_item_in_deal_blocked():
    """Предмет в сделке надевать нельзя: ValidationError, service.equip не вызывается."""
    use_case, service = _make_use_case(inventory_item=_make_inventory_item(deal_id=uuid.uuid4()))

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert "в сделке" in exc_info.value.message
    service.equip.assert_not_awaited()


@pytest.mark.asyncio
async def test_equip_item_not_in_inventory_raises_validation_error():
    """Предмет не найден в инвентаре: get_by_id_and_character возвращает None →
    ValidationError (а не AttributeError → 500)."""
    use_case, service = _make_use_case(inventory_item=None)

    with pytest.raises(ValidationError) as exc_info:
        await use_case(uuid.uuid4(), SimpleNamespace(character_id=uuid.uuid4()))

    assert exc_info.value.field == "inventory_item_id"
    assert "не найден" in exc_info.value.message
    service.equip.assert_not_awaited()


@pytest.mark.asyncio
async def test_repository_dict_building_preserves_deal_id():
    """Имитирует логику репозитория: InventoryItemReadSchema(**item_dict, item=...),
    где item_dict строится из ORM-объекта __dict__.
    До фикса deal_id отбрасывался pydantic (extra='ignore') → AttributeError в equip.py.
    После фикса deal_id сохраняется в схеме и доступен через атрибут."""
    from datetime import datetime, timezone

    # Симуляция ORM-объекта с __dict__, содержащим deal_id
    deal_id = uuid.uuid4()
    item_id = uuid.uuid4()
    character_id = uuid.uuid4()

    class FakeORMItem:
        """Имитация SQLAlchemy ORM-объекта с __dict__ как при joinedload."""
        def __init__(self):
            self.id = item_id
            self.character_id = character_id
            self.shop_id = None
            self.deal_id = deal_id
            self.item_slug = "test.helmet"
            self.amount = 1
            self.expired_date = None
            self.used_count = None
            self.wear = 0
            self.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
            self.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
            self._sa_instance_state = "internal"  # должно отфильтроваться

    orm_obj = FakeORMItem()

    # Логика репозитория: {k: v for k, v in orm_obj.__dict__.items() if k != 'item' and not k.startswith('_')}
    item_dict = {k: v for k, v in orm_obj.__dict__.items() if k != 'item' and not k.startswith('_')}

    # Проверяем что deal_id присутствует в item_dict
    assert "deal_id" in item_dict
    assert item_dict["deal_id"] == deal_id

    # Строим схему как репозиторий
    inventory_item = InventoryItemReadSchema(
        **item_dict,
        item=_make_item_schema(),
    )

    # Ключевая проверка: deal_id сохранён в схеме
    assert inventory_item.deal_id == deal_id

    # Проверяем что equip.py может безопасно обратиться к атрибуту
    # (раньше здесь был AttributeError → 500)
    assert inventory_item.deal_id is not None
