"""Юнит-тесты для SaleItemService (выставление / снятие с продажи, смена цены).

Покрывают проверки лицензии городской лавки:

*Happy path*
    ``add_item_to_sale``     — успешное выставление на продажу при активной лицензии лавки;
    ``update_sale_price``    — успешная смена цены при активной лицензии лавки;
    ``remove_item_from_sale``— успешное снятие с продажи (лицензия НЕ проверяется).

*Негативные сценарии*
    ``CityTradingShopLicenseExpiredError`` — лицензия истекла либо отсутствует
    (``end_license is None``), причём лицензия проверяется и при выставлении на продажу,
    и при изменении цены (новая проверка). Снятие с продажи лицензию не трогает.

Все зависимости конструктора мокаются через ``unittest.mock``:
``AsyncMock`` — для awaitable-методов репозиториев/клиентов/сервисов,
``MagicMock`` — для самих объектов зависимостей.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# --- путь до корня сервиса mining, чтобы импортировать mining_app (как в tests/integration/conftest.py) ---
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from mining_app.apps.items.enums import ItemType  # noqa: E402
from mining_app.apps.items.exceptions import CityTradingShopLicenseExpiredError  # noqa: E402
from mining_app.apps.items.services.sale.sale_items import SaleItemService  # noqa: E402

# ===================== КОНСТАНТЫ =====================

# Обычная торговая локация (НЕ «1.27.trade-hall», чтобы ветка спец-проверок лавки не мешала)
CITY_MARKET_SLUG = "2.20.market"

BASE_ITEM_PRICE = Decimal("100.00")   # базовая цена предмета (для validate_sale_price)
SALE_PRICE = Decimal("150.00")        # цена выставления на продажу (>= base * 0.5)
NEW_SALE_PRICE = Decimal("175.00")    # новая цена при update_sale_price
ITEM_AMOUNT = 5           # количество предметов в инвентарной строке


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ===================== ОКРУЖЕНИЕ =====================

class SaleItemEnvironment:
    """Собирает сервис со всеми моками зависимостей __init__ и хранит артефакты вызовов."""

    def __init__(self, *, shop_location_slug: str = CITY_MARKET_SLUG):
        self.character_id = uuid.uuid4()
        self.inventory_item_id = uuid.uuid4()
        self.shop_id = uuid.uuid4()

        # --- доменные объекты, которые возвращают моки ---
        self.inventory_item = SimpleNamespace(
            id=self.inventory_item_id,
            character_id=self.character_id,
            shop_id=self.shop_id,
            amount=ITEM_AMOUNT,
            item=SimpleNamespace(
                slug="iron_sword",
                price=BASE_ITEM_PRICE,
                item_type=ItemType.WEAPON,
                can_sell=True,
                is_stackable=True,
            ),
        )
        self.shop = SimpleNamespace(
            id=self.shop_id,
            location_slug=shop_location_slug,
            # по умолчанию лицензия активна; негативные тесты переопределяют через _set_license
            end_license=_utc_now() + timedelta(days=3),
        )
        self.grouped_items = SimpleNamespace(character_items=[], sale_items=[], shop_items=[])
        self.created_sale_item = SimpleNamespace(
            id=uuid.uuid4(),
            inventory_item_id=self.inventory_item_id,
            price=SALE_PRICE,
        )

        # --- sale_repository ---
        self.sale_repository = MagicMock(name="SaleInventoryItemRepository")
        self.sale_repository.create = AsyncMock(return_value=self.created_sale_item)
        self.sale_repository.delete = AsyncMock(return_value=None)
        self.sale_repository.update_price = AsyncMock(return_value=None)
        self.sale_repository.get_shop_owner_by_inventory_item = AsyncMock(return_value=self.character_id)
        # по умолчанию предмет ещё НЕ на продаже; happy path update переопределяет
        self.sale_repository.exists = AsyncMock(return_value=False)

        # --- character_item_repository ---
        self.character_item_repository = MagicMock(name="CharacterItemRepository")
        self.character_item_repository.get_by_id = AsyncMock(return_value=self.inventory_item)
        self.character_item_repository.split_amount = AsyncMock(return_value=uuid.uuid4())
        self.character_item_repository.merge_identical_stack = AsyncMock(return_value=None)

        # --- character_item_service ---
        self.character_item_service = MagicMock(name="CharacterItemService")
        self.character_item_service.get_items_from_location = AsyncMock(return_value=self.grouped_items)

        # --- shop_repository ---
        self.shop_repository = MagicMock(name="CityTradingShopCharacterRepository")
        self.shop_repository.get = AsyncMock(return_value=self.shop)

        # --- character_client (в покрытых методах не используется, но обязателен в конструкторе) ---
        self.character_client = MagicMock(name="CharacterServiceClient")
        self.character_client.get_simple_info_character = AsyncMock()
        self.character_client.get_simple_character_balance = AsyncMock()

        # --- redis_publisher (обязателен в конструкторе; публикация событий обёрнута в try/except) ---
        self.redis_publisher = MagicMock(name="RedisPublisher")
        self.redis_publisher.publish = AsyncMock()

        # --- тестируемый сервис ---
        self.service = SaleItemService(
            sale_repository=self.sale_repository,
            character_item_repository=self.character_item_repository,
            character_item_service=self.character_item_service,
            shop_repository=self.shop_repository,
            character_client=self.character_client,
            redis_publisher=self.redis_publisher,
        )


def _set_license(env: SaleItemEnvironment, end_license):
    """Задаёт срок лицензии найденной лавки персонажа."""
    env.shop.end_license = end_license


def _set_item_on_sale(env: SaleItemEnvironment, on_sale: bool):
    """Отмечает, существует ли запись о продаже для inventory_item."""
    env.sale_repository.exists = AsyncMock(return_value=on_sale)


def _assert_no_downstream_effects(env: SaleItemEnvironment):
    """После ошибки лицензии ничего не создаётся, не меняется и не снимается с продажи."""
    env.sale_repository.create.assert_not_awaited()
    env.sale_repository.update_price.assert_not_awaited()
    env.sale_repository.delete.assert_not_awaited()
    env.character_item_repository.split_amount.assert_not_awaited()
    env.character_item_repository.merge_identical_stack.assert_not_awaited()
    env.character_item_service.get_items_from_location.assert_not_awaited()


# ===================== add_item_to_sale =====================

@pytest.mark.asyncio
async def test_add_item_to_sale_happy_path_with_active_license():
    """Активная лицензия лавки: предмет целиком уходит на продажу, цена записана."""
    env = SaleItemEnvironment()  # end_license -> будущая дата

    result = await env.service.add_item_to_sale(
        character_id=env.character_id,
        inventory_item_id=env.inventory_item_id,
        price=SALE_PRICE,
        amount=ITEM_AMOUNT,  # продаём всю строку целиком (amount == inventory_item.amount)
    )

    assert result is env.grouped_items

    # Лавка запрошена по shop_id предмета
    env.shop_repository.get.assert_awaited_once_with(env.shop_id)
    # Владелец проверен по inventory_item
    env.sale_repository.get_shop_owner_by_inventory_item.assert_awaited_once_with(env.inventory_item_id)
    # Предмет продавался целиком => split_amount не нужен, запись о продаже создана сразу
    env.character_item_repository.split_amount.assert_not_awaited()
    env.sale_repository.create.assert_awaited_once_with(env.inventory_item_id, SALE_PRICE)


@pytest.mark.asyncio
async def test_add_item_to_sale_partial_amount_splits_stack_and_creates_sale():
    """Активная лицензия + частичное количество: партия отделяется через split_amount и продаётся."""
    env = SaleItemEnvironment()
    split_item_id = uuid.uuid4()

    async def _fake_split(_inventory_item_id, _amount):
        return split_item_id

    env.character_item_repository.split_amount = AsyncMock(side_effect=_fake_split)

    result = await env.service.add_item_to_sale(
        character_id=env.character_id,
        inventory_item_id=env.inventory_item_id,
        price=SALE_PRICE,
        amount=1,  # меньше ITEM_AMOUNT => ветка частичной продажи
    )

    assert result is env.grouped_items

    env.character_item_repository.split_amount.assert_awaited_once_with(env.inventory_item_id, 1)
    # Запись о продаже создаётся для НОВОЙ отделившейся строки, а не исходной
    env.sale_repository.create.assert_awaited_once_with(split_item_id, SALE_PRICE)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expired_end_license",
    [
        _utc_now() - timedelta(hours=1),  # просроченная лицензия
        None,                             # срок лицензии вовсе не установлен
    ],
    ids=["expired", "none"],
)
async def test_add_item_to_sale_raises_when_license_expired_or_missing(expired_end_license):
    """Истёкшая/отсутствующая лицензия => CityTradingShopLicenseExpiredError до любых изменений."""
    env = SaleItemEnvironment()
    _set_license(env, expired_end_license)

    with pytest.raises(CityTradingShopLicenseExpiredError) as exc_info:
        await env.service.add_item_to_sale(
            character_id=env.character_id,
            inventory_item_id=env.inventory_item_id,
            price=SALE_PRICE,
        )

    error = exc_info.value
    assert error.error_code == "CITY_TRADING_SHOP_LICENSE_EXPIRED"
    assert error.status_code == 403
    assert error.extras["location_slug"] == CITY_MARKET_SLUG

    # Лавку запросили по shop_id, но до проверки владельца дело не дошло
    env.shop_repository.get.assert_awaited_once_with(env.shop_id)
    env.sale_repository.get_shop_owner_by_inventory_item.assert_not_awaited()

    _assert_no_downstream_effects(env)


# ===================== update_sale_price =====================

@pytest.mark.asyncio
async def test_update_sale_price_happy_path_with_active_license():
    """Активная лицензия лавки: цена товара на продаже обновляется."""
    env = SaleItemEnvironment()  # end_license -> будущая дата
    _set_item_on_sale(env, on_sale=True)

    result = await env.service.update_sale_price(
        character_id=env.character_id,
        inventory_item_id=env.inventory_item_id,
        price=NEW_SALE_PRICE,
    )

    assert result is env.grouped_items

    env.shop_repository.get.assert_awaited_once_with(env.shop_id)
    env.sale_repository.get_shop_owner_by_inventory_item.assert_awaited_once_with(env.inventory_item_id)
    env.sale_repository.exists.assert_awaited_once_with(env.inventory_item_id)
    env.sale_repository.update_price.assert_awaited_once_with(env.inventory_item_id, NEW_SALE_PRICE)
    env.sale_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_sale_price_raises_when_license_expired():
    """Новая проверка: изменение цены при истёкшей лицензии => CityTradingShopLicenseExpiredError."""
    env = SaleItemEnvironment()
    _set_license(env, _utc_now() - timedelta(days=1))
    _set_item_on_sale(env, on_sale=True)  # даже если предмет на продаже — цену менять нельзя

    with pytest.raises(CityTradingShopLicenseExpiredError) as exc_info:
        await env.service.update_sale_price(
            character_id=env.character_id,
            inventory_item_id=env.inventory_item_id,
            price=NEW_SALE_PRICE,
        )

    error = exc_info.value
    assert error.error_code == "CITY_TRADING_SHOP_LICENSE_EXPIRED"
    assert error.status_code == 403
    assert error.extras["location_slug"] == CITY_MARKET_SLUG

    # Лицензия проверяется ДО владельца и факта «на продаже»
    env.sale_repository.get_shop_owner_by_inventory_item.assert_not_awaited()
    env.sale_repository.exists.assert_not_awaited()

    _assert_no_downstream_effects(env)


# ===================== remove_item_from_sale =====================

@pytest.mark.asyncio
async def test_remove_item_from_sale_happy_path_without_license_check():
    """Снятие с продажи проходит без проверки лицензии: лавка вовсе не запрашивается."""
    env = SaleItemEnvironment()
    # Подстраховка: даже формально «просроченная» лицензия (None) не должна мешать снятию
    _set_license(env, None)

    result = await env.service.remove_item_from_sale(
        character_id=env.character_id,
        inventory_item_id=env.inventory_item_id,
        amount=None,  # забрать всё => строка продажи удаляется
    )

    assert result is env.grouped_items

    # ГЛАВНОЕ: снятие с продажи НЕ проверяет лицензию. Лавка запрашивается ровно один раз —
    # только ради payload события (location_slug), но НЕ для проверки срока лицензии:
    # при end_license=None (см. _set_license выше) операция всё равно завершилась успешно.
    env.shop_repository.get.assert_awaited_once_with(env.shop_id)

    # Строка продажи удалена, стек слит обратно в инвентарь
    env.sale_repository.delete.assert_awaited_once_with(env.inventory_item_id)
    env.character_item_repository.merge_identical_stack.assert_awaited_once_with(env.inventory_item_id)
    env.character_item_service.get_items_from_location.assert_awaited_once_with(env.character_id)

    # Мутаций продажи другого рода быть не должно
    env.sale_repository.create.assert_not_awaited()
    env.sale_repository.update_price.assert_not_awaited()
