"""Интеграционные тесты БИРЖИ/СКУПКИ (economy) на РЕАЛЬНОЙ тестовой БД.

Продакшн-БД (economy_service) НЕ используется. Подключение только к
отдельной базе echo_test на порту 5552 (см. ECHO_TEST_ECONOMY_DB_DSN).
Внешние HTTP-зависимости (characters/mining) замоканы фейками.
"""

import asyncio
import os
import sys
from decimal import Decimal

import pytest
import sqlalchemy as sa

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncpg  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

# Импорт core.db создаёт движок приложения на продакшн-БД, но соединений
# он не открывает — в тестах этот глобальный движок не используется.
from economy_app.core.db import Base  # noqa: E402
from economy_app.apps.pawn_shop import models as eco_models  # noqa: E402,F401
from economy_app.apps.pawn_shop.use_cases.buyout.buy import BuyResourceFromBuyoutUseCase  # noqa: E402
from economy_app.apps.pawn_shop.use_cases.buyout.sell import SellResourceToBuyoutUseCase  # noqa: E402

TEST_DB_DSN = os.environ.get(
    "ECHO_TEST_ECONOMY_DB_DSN",
    "postgresql+asyncpg://postgres:password@localhost:5552/echo_test",
)
ADMIN_DB_NAME = "postgres"
TEST_DB_NAME = TEST_DB_DSN.rsplit("/", 1)[1]


async def _ensure_database_exists() -> None:
    plain_dsn = TEST_DB_DSN.replace("postgresql+asyncpg://", "postgresql://")
    admin_dsn = plain_dsn.rsplit("/", 1)[0] + f"/{ADMIN_DB_NAME}"
    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def engine():
    asyncio.run(_ensure_database_exists())

    async def _reset_schema(eng):
        async with eng.begin() as conn:
            await conn.execute(sa.text("DROP SCHEMA public CASCADE"))
            await conn.execute(sa.text("CREATE SCHEMA public"))

    eng = create_async_engine(TEST_DB_DSN, poolclass=NullPool)
    asyncio.run(_reset_schema(eng))
    asyncio.run(eng.dispose())
    eng = create_async_engine(TEST_DB_DSN, poolclass=NullPool)

    async def _create_tables(eng):
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables(eng))
    yield eng
    asyncio.run(eng.dispose())


_TABLE_LIST = ", ".join(f'"{name}"' for name in Base.metadata.tables)


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(engine):
    async with engine.connect() as conn:
        await conn.execute(sa.text(f"TRUNCATE TABLE {_TABLE_LIST} RESTART IDENTITY CASCADE"))
        await conn.commit()
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session


# ==========================================================================
# Фейки внешних сервисов
# ==========================================================================

def http_status_error(code: int = 409) -> Exception:
    import httpx
    req = httpx.Request("POST", "http://fake")
    resp = httpx.Response(code, request=req)
    return httpx.HTTPStatusError(f"{code}", request=req, response=resp)


class FakeCharactersClient:
    def __init__(self) -> None:
        self.balance = Decimal("1000000")
        self.trade_license = {"exchange_tax_rate": "0.15"}
        self.calls: list = []
        self._fail: dict = {}
        self._fail_on_call_index: list = []  # (method, zero_based_index, exc)

    def fail_on(self, method: str, exc: Exception) -> None:
        self._fail[method] = exc

    def fail_on_call_index(self, method: str, index: int, exc: Exception) -> None:
        self._fail_on_call_index.append((method, index, exc))

    def _maybe_fail(self, method: str) -> None:
        if method in self._fail:
            raise self._fail[method]
        matched = [(m, i, e) for m, i, e in self._fail_on_call_index if m == method]
        for m, idx, exc in matched:
            done = sum(1 for c in self.calls if c[0] == m)
            if done == idx:  # это вызов номер idx (0-based) данного метода
                raise exc

    async def get_balance(self, character_id) -> Decimal:
        self.calls.append(("get_balance", character_id))
        return self.balance

    async def get_trade_license(self, character_id):
        self.calls.append(("get_trade_license", character_id))
        return dict(self.trade_license)

    async def get_character_name(self, character_id) -> str:
        return f"Char-{str(character_id)[:8]}"

    async def debit(self, character_id, amount, **kw):
        call = ("debit", character_id, Decimal(amount), kw.get("operation_id"))
        self.calls.append(call)
        self._maybe_fail("debit")
        return {}

    async def credit(self, character_id, amount, **kw):
        call = ("credit", character_id, Decimal(amount), kw.get("operation_id"))
        self.calls.append(call)
        self._maybe_fail("credit")
        return {}

    async def get_character_location(self, character_id) -> str:
        return "1.13.forge"



class FakeMiningClient:
    def __init__(self) -> None:
        self.player_resources: list = []
        self.trade_license = {"exchange_tax_rate": "0.15"}
        self.calls: list = []
        self._fail: dict = {}

    def fail_on(self, method: str, exc: Exception) -> None:
        self._fail[method] = exc

    def _record(self, method, resource_slug, character_id, amount):
        self.calls.append((method, resource_slug, character_id, amount))
        if method in self._fail:
            raise self._fail[method]
        return {}

    async def debit(self, resource_slug, character_id, amount, operation_id):
        return self._record("debit", resource_slug, character_id, amount)

    async def credit(self, resource_slug, character_id, amount, operation_id):
        return self._record("credit", resource_slug, character_id, amount)

    async def get_player_resources(self, character_id):
        return {"resources": [dict(r) for r in self.player_resources]}

    async def get_trade_license(self, character_id):
        return dict(self.trade_license)


class FakePublisher:
    def __init__(self) -> None:
        self.published: list = []

    async def publish(self, channel: str, payload: dict) -> None:
        self.published.append((channel, payload))


class FakeEvents:
    def __init__(self) -> None:
        self.published: list = []
        self.publisher = FakePublisher()

    async def publish_message(self, message):
        self.published.append(message)

    async def publish_state_update(self, *a, **k):
        pass


class FakeTemplates:
    def _plural_briquet(self, n: int) -> str:
        return "briquet"

    def get_buyout_buy_message(self, items_list: str, price: str) -> str:
        return f"buy {items_list} {price}"

    def get_buyout_sell_message(self, items_list: str, price: str) -> str:
        return f"sell {items_list} {price}"

    def get_exchange_deal_buy_executor_message(self, items: str, price: str) -> str:
        return f"ex-buy-executor {items} {price}"

    def get_exchange_deal_sell_executor_message(self, items: str, price: str, tax: str) -> str:
        return f"ex-sell-executor {items} {price} {tax}"

    def get_exchange_deal_sell_owner_message(self, items: str, price: str, executor_name: str, tax: str) -> str:
        return f"ex-sell-owner {items} {price} {executor_name} {tax}"

    def get_exchange_deal_buy_owner_message(self, items: str, price: str, executor_name: str) -> str:
        return f"ex-buy-owner {items} {price} {executor_name}"



@pytest.fixture
def char_client():
    return FakeCharactersClient()


@pytest.fixture
def mining_client():
    mining = FakeMiningClient()
    return mining


@pytest.fixture
def ucs(db_session, char_client, mining_client):
    from economy_app.apps.pawn_shop.use_cases.exchange.create import CreateExchangeLotUseCase
    from economy_app.apps.pawn_shop.use_cases.exchange.deal import DealExchangeLotUseCase
    from economy_app.apps.pawn_shop.use_cases.exchange.cancel import CancelExchangeLotUseCase

    events = FakeEvents()
    templates = FakeTemplates()
    return {
        "buy": BuyResourceFromBuyoutUseCase(char_client, mining_client, events, templates),
        "sell": SellResourceToBuyoutUseCase(char_client, mining_client, events, templates),
        "create_lot": CreateExchangeLotUseCase(char_client, mining_client),
        "deal_lot": DealExchangeLotUseCase(char_client, mining_client, events, templates),
        "cancel_lot": CancelExchangeLotUseCase(char_client, mining_client),
        "events": events,
        "char_client": char_client,
        "mining_client": mining_client,
    }


async def seed_resource(session, code="iron", name="Iron", tradeable=True,
                        sell_price="12.00", buy_price="8.00", stock=100):
    resource = eco_models.Resource(
        external_resource_id=f"ext-{code}", code=code, name=name,
        source_type=(eco_models.ResourceSourceType.RESOURCE_LOCATION if tradeable
                     else eco_models.ResourceSourceType.CITY_LOCATION),
        is_tradeable=tradeable, initial_price=Decimal("10.00"),
        category=eco_models.ResourceCategory.MINE, order=1,
    )
    session.add(resource)
    await session.flush()
    if sell_price is not None:
        session.add(eco_models.CurrentPrice(
            resource_id=resource.id,
            sell_price=Decimal(sell_price), buy_price=Decimal(buy_price)))
    if stock is not None:
        session.add(eco_models.BuyoutStock(resource_id=resource.id, quantity=stock))
    await session.commit()
    return resource

