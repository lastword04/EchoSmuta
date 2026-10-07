"""Юнит-тесты для CreateItemsCreatingActionService.

Покрывают новые сценарии проверки лицензий:

*Happy path*
    Успешный старт крафта нового предмета при активной лицензии мастера
    (production-локация «кузница») и активной лицензии городской лавки.

*Production-локации (кузница / ювелирная)*
    ``NoCraftingLicenseError`` — лицензия мастера неактивна;
    ``RuntimeError``          — сервис лицензий вообще не передан в конструктор.

*Обычные городские лавки (не production)*
    ``CityTradingShopLicenseExpiredError`` — лицензия лавки истекла либо отсутствует;
    ``CityTradingShopNotFoundError``       — у персонажа нет лавки в этой локации.

Все зависимости конструктора мокаются через ``unittest.mock``:
``AsyncMock`` — для awaitable-методов репозиториев/клиентов/сервисов,
``MagicMock`` — для синхронных методов и celery-задачи.
"""

import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# --- путь до корня сервиса mining, чтобы импортировать mining_app (как в tests/integration/conftest.py) ---
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from mining_app.apps.items.enums import ItemCreatingStatus
from mining_app.apps.items.exceptions import (
    CityTradingShopLicenseExpiredError,
    CityTradingShopNotFoundError,
    NoCraftingLicenseError,
)
from mining_app.apps.items.services.crafting.items_creating_actions import (
    PRODUCTION_LOCATION_SLUGS,
    CreateItemsCreatingActionService,
)

# ===================== КОНСТАНТЫ =====================

FORGE_LOCATION = "1.13.forge"
JEWELERS_LOCATION = "1.16.jewelers"

# Обычная (не production) локация крафта — идёт через проверку городской лавки
CITY_SHOP_ITEM_LOCATION = "2.10.tannery"

FORGE_MARKET_SLUG = "1.14.market"    # торговая локация здания кузницы
TANNERY_MARKET_SLUG = "2.20.market"  # торговая локация обычной мастерской

ITEM_SLUG = "iron_sword"
RECIPE_MESSAGE = "Крафт запущен: этап 1 из 3"
COOLDOWN_SECONDS = 60


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ===================== ОКРУЖЕНИЕ =====================

class CraftingEnvironment:
    """Собирает сервис со всеми моками зависимостей __init__ и хранит артефакты вызовов."""

    def __init__(
        self,
        *,
        item_location_slug: str,
        city_trading_location_slug: str,
        building_location_slug: str | None = None,
        with_license_service: bool = True,
    ):
        self.character_id = uuid.uuid4()
        self.recipe_id = uuid.uuid4()
        self.building_location_slug = building_location_slug or item_location_slug
        self.city_trading_location_slug = city_trading_location_slug

        # --- доменные объекты, которые возвращают моки ---
        self.character = SimpleNamespace(
            id=self.character_id,
            location_slug=self.building_location_slug,
            level=10,
            tiredness=0.1,
        )
        self.recipe = SimpleNamespace(id=self.recipe_id, item_slug=ITEM_SLUG, quantity=1)
        self.item = SimpleNamespace(
            slug=ITEM_SLUG,
            name="Меч из болотной стали",
            location_slug=item_location_slug,
            craft_stages=3,
        )
        self.building = SimpleNamespace(
            location_slug=self.building_location_slug,
            city_trading_location_slug=city_trading_location_slug,
        )
        self.component = SimpleNamespace(
            resource_slug="iron_ore",
            resource_name="Железная руда",
            quantity=2,
        )

        # --- repository ---
        self.repository = MagicMock(name="ItemsCreatingActionRepository")
        self.repository.create = AsyncMock(side_effect=self._fake_create)
        self.repository.update_celery_task_id = AsyncMock(side_effect=self._fake_update_task_id)

        # --- character_service (адаптер к characters-сервису) ---
        self.character_service = MagicMock(name="CharacterServiceClient")
        self.character_service.get_simple_info_character = AsyncMock(return_value=self.character)

        # --- building_repository ---
        self.building_repository = MagicMock(name="BuildingRepository")
        self.building_repository.get_by_city_trading_location = AsyncMock(return_value=self.building)

        # --- item_service ---
        self.item_service = MagicMock(name="ItemService")
        self.item_service.get_by_slug = AsyncMock(return_value=self.item)

        # --- character_resource_service (персонажу хватает ресурсов) ---
        self.character_resource_service = MagicMock(name="CharacterResourceService")

        async def _enough_resource(_character_id, _resource_slug):
            return SimpleNamespace(amount=999)

        self.character_resource_service.get_by_character_and_resource = AsyncMock(
            side_effect=_enough_resource
        )

        # --- item_component_service ---
        self.item_component_service = MagicMock(name="ItemComponentService")
        self.item_component_service.get_components_with_resource_names = AsyncMock(
            return_value=[self.component]
        )

        # --- city_trading_shop_repository (по умолчанию магазина нет; тесты переопределяют) ---
        self.city_trading_shop_repository = MagicMock(name="CityTradingShopRepository")
        self.city_trading_shop_repository.get_by_location_and_character = AsyncMock(return_value=None)

        # --- character_recipes_repository ---
        self.character_recipes_repository = MagicMock(name="CharacterRecipesRepository")
        self.character_recipes_repository.get_for_character = AsyncMock(return_value=self.recipe)
        self.character_recipes_repository.decrement_quantity_for_character = AsyncMock()

        # --- character_start_creating_repository ---
        self.character_start_creating_repository = MagicMock(
            name="CharacterStartCreatingItemRepository"
        )
        self.character_start_creating_repository.get_by_character_and_item = AsyncMock(
            return_value=None
        )
        # сервис создаёт запись CharacterStartCreatingItem (craft_stage=0) и коммитит сессию
        self.character_start_creating_repository.create = AsyncMock(
            return_value=SimpleNamespace(id=uuid.uuid4())
        )
        self.character_start_creating_repository.session = MagicMock()
        self.character_start_creating_repository.session.commit = AsyncMock()

        # --- template_service (методы синхронные -> MagicMock) ---
        self.template_service = MagicMock(name="ItemTemplateService")
        self.template_service.get_crafting_progress_message = MagicMock(return_value=RECIPE_MESSAGE)

        # --- items_events ---
        self.items_events = MagicMock(name="ItemEvents")
        self.items_events.publish_message = AsyncMock()

        # --- captcha_adapter (B1: verify вызывается внутри creator после всех проверок) ---
        self.captcha = SimpleNamespace(captcha_id="test-captcha-id", user_input="1234")
        self.captcha_adapter = MagicMock(name="CaptchaAdapter")
        self.captcha_adapter.verify_captcha = AsyncMock(return_value=None)

        # --- crafting_license_service (опциональная зависимость) ---
        self.crafting_license_service = None
        if with_license_service:
            license_service = MagicMock(name="CraftingLicenseService")
            license_service.get_status = AsyncMock(return_value=SimpleNamespace(is_active=True))
            self.crafting_license_service = license_service

        self.service = CreateItemsCreatingActionService(
            repository=self.repository,
            character_service=self.character_service,
            building_repository=self.building_repository,
            item_service=self.item_service,
            character_resource_service=self.character_resource_service,
            item_component_service=self.item_component_service,
            city_trading_shop_repository=self.city_trading_shop_repository,
            character_recipes_repository=self.character_recipes_repository,
            character_start_creating_repository=self.character_start_creating_repository,
            captcha_adapter=self.captcha_adapter,
            template_service=self.template_service,
            items_events=self.items_events,
            cooldown_seconds=COOLDOWN_SECONDS,
            crafting_license_service=self.crafting_license_service,
        )

        # --- артефакты вызовов ---
        self.create_input = None
        self.created_action = None
        self.updated_action = None
        self.celery_task_id_used = None

    # --- side_effect'ы репозитория крафт-действий ---
    def _fake_create(self, create_schema):
        self.create_input = create_schema
        self.created_action = SimpleNamespace(id=uuid.uuid4())
        return self.created_action

    def _fake_update_task_id(self, *, action_id, celery_task_id):
        assert action_id == self.created_action.id
        self.celery_task_id_used = celery_task_id
        self.updated_action = SimpleNamespace(
            id=action_id,
            celery_task_id=celery_task_id,
            status=ItemCreatingStatus.IN_PROGRESS,
        )
        return self.updated_action

def _forge_environment(**kwargs) -> CraftingEnvironment:
    """Окружение для production-локации «кузница»."""
    return CraftingEnvironment(
        item_location_slug=FORGE_LOCATION,
        city_trading_location_slug=FORGE_MARKET_SLUG,
        **kwargs,
    )


def _jewelers_environment(**kwargs) -> CraftingEnvironment:
    """Окружение для production-локации «ювелирная»."""
    return CraftingEnvironment(
        item_location_slug=JEWELERS_LOCATION,
        city_trading_location_slug=FORGE_MARKET_SLUG,
        **kwargs,
    )


def _city_shop_environment(**kwargs) -> CraftingEnvironment:
    """Окружение для обычной (не production) локации крафта."""
    return CraftingEnvironment(
        item_location_slug=CITY_SHOP_ITEM_LOCATION,
        city_trading_location_slug=TANNERY_MARKET_SLUG,
        **kwargs,
    )


def _set_shop(env: CraftingEnvironment, end_license):
    """Настраивает найденную лавку персонажа с заданным сроком лицензии."""
    shop = SimpleNamespace(end_license=end_license)
    env.city_trading_shop_repository.get_by_location_and_character = AsyncMock(return_value=shop)
    return shop


async def _start_new_craft(env: CraftingEnvironment):
    return await env.service.create_new_item_crafting_action(
        character_id=env.character_id,
        recipe_id=env.recipe_id,
        captcha=env.captcha,
    )


def _assert_no_downstream_effects(env: CraftingEnvironment):
    """После ошибки на стадии лицензий ничего не создастся, не спишется и не уйдёт в celery."""
    env.captcha_adapter.verify_captcha.assert_not_awaited()
    env.repository.create.assert_not_awaited()
    env.repository.update_celery_task_id.assert_not_awaited()
    env.character_recipes_repository.decrement_quantity_for_character.assert_not_awaited()
    env.item_component_service.get_components_with_resource_names.assert_not_awaited()

@pytest.fixture()
def finish_creating_task():
    """Подменяет celery-задачу finish_creating_task, чтобы тесты не ходили в брокер."""
    with patch("mining_app.apps.items.tasks.finish_creating_task") as task_mock:
        calls = []

        def _record(args=None, countdown=None, task_id=None, **kwargs):
            calls.append({"args": args or [], "countdown": countdown, "task_id": task_id})
            return SimpleNamespace(id=task_id)

        task_mock.apply_async.side_effect = _record
        task_mock.calls = calls
        yield task_mock


# ===================== ТЕСТЫ =====================


def test_production_location_slugs_are_forge_and_jewelers():
    """Страховка: набор production-локаций в исходнике не изменился незаметно."""
    assert PRODUCTION_LOCATION_SLUGS == {FORGE_LOCATION, JEWELERS_LOCATION}


@pytest.mark.asyncio
async def test_create_new_item_success_with_active_license(finish_creating_task):
    """HAPPY PATH: активная лицензия мастера -> крафт нового предмета создаётся."""
    env = _forge_environment()  # crafting_license_service.get_status -> is_active=True

    result = await env.service.create_new_item_crafting_action(
        character_id=env.character_id,
        recipe_id=env.recipe_id,
        captcha=env.captcha,
    )

    # B1: капча сжигается после всех проверок — ровно один раз
    env.captcha_adapter.verify_captcha.assert_awaited_once_with(env.captcha)

    # Лицензия мастера проверена ровно один раз и для нужной production-локации
    env.crafting_license_service.get_status.assert_awaited_once_with(env.character_id, FORGE_LOCATION)
    # Routing: у production-локации городская лавка НЕ проверяется
    env.city_trading_shop_repository.get_by_location_and_character.assert_not_awaited()

    # Создано корректное крафт-действие
    assert env.create_input.character_id == env.character_id
    assert env.create_input.location_slug == env.building_location_slug
    assert env.create_input.status is ItemCreatingStatus.IN_PROGRESS
    assert env.create_input.quantity is None
    assert env.create_input.craft_stage == 0
    assert env.create_input.message == RECIPE_MESSAGE
    assert env.create_input.finish_time - env.create_input.start_time == timedelta(
        seconds=COOLDOWN_SECONDS
    )

    # Celery-задача запланирована с правильными аргументами
    assert len(finish_creating_task.calls) == 1
    call = finish_creating_task.calls[0]
    assert call["args"] == [
        env.created_action.id,
        {"id": str(env.character_id), "location_slug": env.character.location_slug},
        ITEM_SLUG,
    ]
    assert call["countdown"] == COOLDOWN_SECONDS
    assert call["task_id"] == f"finish_creating:{env.created_action.id}"

    # Действие обновлено celery_task_id, рецепт списан, результат возвращён
    assert env.celery_task_id_used == call["task_id"]
    env.repository.update_celery_task_id.assert_awaited_once_with(
        action_id=env.created_action.id,
        celery_task_id=call["task_id"],
    )
    env.character_recipes_repository.decrement_quantity_for_character.assert_awaited_once_with(
        env.recipe_id, env.character_id
    )
    assert result is env.updated_action
    assert result.celery_task_id == call["task_id"]

@pytest.mark.parametrize("location_slug", sorted(PRODUCTION_LOCATION_SLUGS))
@pytest.mark.asyncio
async def test_inactive_master_license_raises_no_crafting_license_error(
    finish_creating_task, location_slug
):
    """Кузница/ювелирная + неактивная лицензия мастера => NoCraftingLicenseError."""
    env_builder = {
        FORGE_LOCATION: _forge_environment,
        JEWELERS_LOCATION: _jewelers_environment,
    }[location_slug]
    env = env_builder()
    env.crafting_license_service.get_status = AsyncMock(
        return_value=SimpleNamespace(is_active=False)
    )

    with pytest.raises(NoCraftingLicenseError) as exc_info:
        await _start_new_craft(env)

    error = exc_info.value
    assert error.error_code == "NO_CRAFTING_LICENSE"
    assert error.status_code == 403
    assert error.extras["location_slug"] == location_slug

    # Лицензию проверили только по своей production-локации
    env.crafting_license_service.get_status.assert_awaited_once_with(env.character_id, location_slug)

    _assert_no_downstream_effects(env)
    # Celery-задача тоже не должна планироваться
    assert finish_creating_task.calls == []


@pytest.mark.asyncio
async def test_production_location_without_license_service_raises_runtime_error(
    finish_creating_task,
):
    """Если сервис лицензий не передан, production-крафт падает с RuntimeError, а не молчит."""
    env = _forge_environment(with_license_service=False)

    with pytest.raises(RuntimeError, match="Crafting license service is not available"):
        await _start_new_craft(env)

    _assert_no_downstream_effects(env)
    assert finish_creating_task.calls == []

@pytest.mark.parametrize(
    "expired_end_license",
    [
        _utc_now() - timedelta(hours=1),  # просроченная лицензия
        None,                             # срок лицензии вовсе не установлен
    ],
)
@pytest.mark.asyncio
async def test_expired_city_shop_license_raises_license_expired_error(
    finish_creating_task, expired_end_license
):
    """Обычная лавка с истёкшей/отсутствующей лицензией => CityTradingShopLicenseExpiredError."""
    env = _city_shop_environment()
    _set_shop(env, end_license=expired_end_license)

    with pytest.raises(CityTradingShopLicenseExpiredError) as exc_info:
        await _start_new_craft(env)

    error = exc_info.value
    assert error.error_code == "CITY_TRADING_SHOP_LICENSE_EXPIRED"
    assert error.status_code == 403
    assert error.extras["location_slug"] == TANNERY_MARKET_SLUG
    if expired_end_license is None:
        assert "end_license" not in error.extras
    else:
        assert error.extras["end_license"] == str(expired_end_license)

    env.city_trading_shop_repository.get_by_location_and_character.assert_awaited_once_with(
        location_slug=TANNERY_MARKET_SLUG,
        character_id=env.character_id,
    )
    # Routing: сервис лицензий мастера на городском пути не затрагивается вовсе
    env.crafting_license_service.get_status.assert_not_awaited()

    _assert_no_downstream_effects(env)
    assert finish_creating_task.calls == []

@pytest.mark.asyncio
async def test_missing_city_shop_raises_city_shop_not_found_error(finish_creating_task):
    """Лавки у персонажа нет вовсе => CityTradingShopNotFoundError."""
    env = _city_shop_environment()  # get_by_location_and_character -> None по умолчанию

    with pytest.raises(CityTradingShopNotFoundError) as exc_info:
        await _start_new_craft(env)

    error = exc_info.value
    assert error.error_code == "CITY_TRADING_SHOP_NOT_FOUND"
    assert error.status_code == 404
    assert error.extras["location_slug"] == TANNERY_MARKET_SLUG
    assert error.extras["character_id"] == str(env.character_id)

    env.city_trading_shop_repository.get_by_location_and_character.assert_awaited_once_with(
        location_slug=TANNERY_MARKET_SLUG,
        character_id=env.character_id,
    )
    env.crafting_license_service.get_status.assert_not_awaited()

    _assert_no_downstream_effects(env)
    assert finish_creating_task.calls == []


@pytest.mark.asyncio
async def test_active_city_shop_license_starts_craft(finish_creating_task):
    """HAPPY PATH городской ветки: действующая лицензия лавки пропускает дальше."""
    env = _city_shop_environment()
    future_license = _utc_now() + timedelta(days=5)
    _set_shop(env, end_license=future_license)

    result = await env.service.create_new_item_crafting_action(
        character_id=env.character_id,
        recipe_id=env.recipe_id,
        captcha=env.captcha,
    )

    env.captcha_adapter.verify_captcha.assert_awaited_once_with(env.captcha)
    assert result is env.updated_action
    assert env.create_input.location_slug == env.building_location_slug
    assert env.create_input.craft_stage == 0

    assert len(finish_creating_task.calls) == 1
    call = finish_creating_task.calls[0]
    assert call["args"][0] == env.created_action.id
    assert call["countdown"] == COOLDOWN_SECONDS

    env.character_recipes_repository.decrement_quantity_for_character.assert_awaited_once_with(
        env.recipe_id, env.character_id
    )
    # Ветка города никогда не спрашивает лицензию мастера
    env.crafting_license_service.get_status.assert_not_awaited()










