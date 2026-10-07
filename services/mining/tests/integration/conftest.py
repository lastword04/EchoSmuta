"""Интеграционные тесты модуля СДЕЛОК (mining) на РЕАЛЬНОЙ тестовой БД.

Продакшн-БД (mining_service) НЕ используется. Подключение выполняется
только к отдельной базе echo_test на том же инстансе PostgreSQL:

    postgresql+asyncpg://postgres:password@127.0.0.1:5551/echo_test

DSN переопределяется переменной окружения ECHO_TEST_MINING_DB_DSN.

Схема создаётся из SQLAlchemy-метаданных приложения (create_all),
между тестами таблицы очищаются через TRUNCATE ... CASCADE.

Внешние HTTP-сервисы (characters) замоканы фейком FakeCharacterClient,
при этом репозитории и use-cases работают с реальной БД.
"""

import asyncio
import os
import sys
import uuid as uuid_mod
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
import sqlalchemy as sa

# --- путь до корня сервиса mining, чтобы импортировать mining_app и shared ---
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncpg  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from shared.enums import UserRole  # noqa: E402
from shared.schemas.auth import UserTokenDataReadSchema  # noqa: E402

# Регистрируем ВСЕ модели приложения в метаданных
from mining_app.core.db import Base  # noqa: E402
from mining_app.apps.resources import models as _resources_models  # noqa: E402,F401
from mining_app.apps.items import models as _items_models  # noqa: E402,F401
from mining_app.apps.items.deals import models as _deals_models  # noqa: E402,F401

from mining_app.apps.items.deals.repositories import (  # noqa: E402
    DealItemRepository,
    DealLedgerOperationRepository,
    DealOfferRepository,
    DealRepository,
    DealResourceReservationRepository,
    TradeLicenseRepository,
)
from mining_app.apps.items.deals.use_cases import (
    AddDealResourceUseCase,
    CancelDealUseCase,
    CompleteDealUseCase,
    ConfirmDealUseCase,
    CreateDealUseCase,
    ExpireDealUseCase,
    RecoverCompletingDealsUseCase,
    SetDealDucatsUseCase,
    SetDealGoldUseCase,
)

TEST_DB_DSN = os.environ.get(
    "ECHO_TEST_MINING_DB_DSN",
    "postgresql+asyncpg://postgres:password@127.0.0.1:5551/echo_test",
)
ADMIN_DB_NAME = "postgres"
TEST_DB_NAME = TEST_DB_DSN.rsplit("/", 1)[1]

DEAL_LOCATION = "1.13.forge"


# ==========================================================================
# Инфраструктура тестовой БД
# ==========================================================================

async def _ensure_database_exists() -> None:
    # asyncpg не понимает схему postgresql+asyncpg:// — убираем её
    plain_dsn = TEST_DB_DSN.replace("postgresql+asyncpg://", "postgresql://")
    admin_dsn = plain_dsn.rsplit("/", 1)[0] + f"/{ADMIN_DB_NAME}"
    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def engine():
    """Отдельный движок на тестовую БД. NullPool — каждое соединение живёт в
    цикле событий конкретного теста, пул между тестами не переиспользуется."""
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




# ==========================================================================
# Фейк клиента сервиса персонажей (единственная внешняя зависимость сделок)
# ==========================================================================

class FakeCharacterClient:
    def __init__(self) -> None:
        self.online_ids: set = set()
        self.locations: dict = {}
        self.ducats_balances: dict = {}
        self.gold_balances: dict = {}
        self.weight_balances: dict = {}
        self.gold_trade_enabled = True
        self.calls: list[tuple] = []
        self._fail: dict = {}

    def fail_on(self, method: str, exc: Exception) -> None:
        self._fail[method] = exc

    def _record(self, method, cid, amount, operation_id=None, **kwargs):
        self.calls.append((method, cid, amount, operation_id))
        if method in self._fail:
            raise self._fail[method]
        return SimpleNamespace(status="ok")

    async def get_online_characters(self, location_slug):
        objects = [SimpleNamespace(id=cid) for cid in self.online_ids]
        return SimpleNamespace(objects=objects)

    async def get_full_character(self, character_id):
        return SimpleNamespace(
            location_slug=self.locations.get(character_id, DEAL_LOCATION),
            gold=self.gold_balances.get(character_id, Decimal("0")),
        )

    async def get_simple_info_character(self, character_id):
        return SimpleNamespace(name=f"Char-{str(character_id)[:8]}")

    async def get_character_weight_balance(self, character_id):
        return self.weight_balances.get(
            character_id, SimpleNamespace(weight=0, max_weight=10000)
        )

    async def get_simple_character_balance(self, character_id):
        return SimpleNamespace(ducats=self.ducats_balances.get(character_id, Decimal("100000")))

    async def get_trade_privileges(self, character_id):
        return SimpleNamespace(gold_trade_enabled=self.gold_trade_enabled)

    async def debit_ducats(self, character_id, amount, operation_id=None,
                           operation_type=None, source=None, counterparty_id=None,
                           item_meta=None, meta=None, **kw):
        return self._record("debit_ducats", character_id, amount, operation_id)

    async def credit_ducats(self, character_id, amount, operation_id=None,
                            operation_type=None, source=None, counterparty_id=None,
                            item_meta=None, meta=None, **kw):
        return self._record("credit_ducats", character_id, amount, operation_id)

    async def debit_gold(self, character_id, amount, operation_id=None,
                         operation_type=None, source=None, item_meta=None,
                         counterparty_id=None, **kw):
        return self._record("debit_gold", character_id, amount, operation_id)

    async def credit_gold(self, character_id, amount, operation_id=None,
                          operation_type=None, source=None, item_meta=None,
                          counterparty_id=None, **kw):
        return self._record("credit_gold", character_id, amount, operation_id)


class FakeDealEvents:
    def __init__(self) -> None:
        self.events: list = []

    async def publish_deal_event(self, event):
        self.events.append((event.event_type, event.deal_id, event.details))


# ==========================================================================
# Хелперы и фикстуры данных
# ==========================================================================

_serial_counter = {"n": 0}


async def seed_resource(session, slug="iron", price=100, weight=2, name="Железо"):
    _serial_counter["n"] += 1
    resource = _resources_models.Resource(
        name=name, slug=slug, weight=weight, price=price,
        serial_number=_serial_counter["n"],
    )
    session.add(resource)
    await session.commit()
    return resource


async def seed_character_resource(session, character_id, slug, amount):
    row = _resources_models.CharacterResource(
        character_id=character_id, resource_slug=slug, amount=amount
    )
    session.add(row)
    await session.commit()
    return row


def user(character_id) -> UserTokenDataReadSchema:
    return UserTokenDataReadSchema(
        user_id=uuid_mod.uuid4(),
        character_id=character_id,
        role=UserRole.USER,
        is_main=True,
        expiration=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture
def char_client():
    return FakeCharacterClient()


@pytest.fixture
def events():
    return FakeDealEvents()


@pytest.fixture
def ucs(db_session, char_client, events):
    """Пачка use-cases с реальными репозиториями поверх тестовой БД."""
    repo = DealRepository(db_session)
    offer_repo = DealOfferRepository(db_session)
    item_repo = DealItemRepository(db_session)
    res_repo = DealResourceReservationRepository(db_session)
    ledger_repo = DealLedgerOperationRepository(db_session)
    lic_repo = TradeLicenseRepository(db_session)

    complete_uc = CompleteDealUseCase(
        repo, offer_repo, item_repo, res_repo, ledger_repo, lic_repo,
        char_client, deal_tax=0.10, discounted_tax=0.03, deal_events=events,
    )
    confirm_uc = ConfirmDealUseCase(
        repo, offer_repo, item_repo, complete_uc, char_client, deal_events=events,
    )
    return SimpleNamespace(
        session=db_session,
        char_client=char_client,
        events=events,
        repo=repo,
        offer_repo=offer_repo,
        item_repo=item_repo,
        res_repo=res_repo,
        ledger_repo=ledger_repo,
        complete_uc=complete_uc,
        confirm_uc=confirm_uc,
        create_uc=CreateDealUseCase(repo, offer_repo, char_client, deal_events=events),
        set_ducats_uc=SetDealDucatsUseCase(
            repo, offer_repo, item_repo, ledger_repo, char_client, deal_events=events,
        ),
        set_gold_uc=SetDealGoldUseCase(
            repo, offer_repo, item_repo, ledger_repo, char_client, deal_events=events,
        ),
        add_res_uc=AddDealResourceUseCase(
            repo, offer_repo, item_repo, res_repo, char_client, deal_events=events,
        ),
        cancel_uc=CancelDealUseCase(
            repo, offer_repo, item_repo, res_repo, ledger_repo,
            deal_events=events, character_client=char_client,
        ),
        expire_uc=ExpireDealUseCase(
            repo, offer_repo, item_repo, res_repo, ledger_repo, char_client,
            deal_events=events,
        ),
        recover_uc=RecoverCompletingDealsUseCase(repo, complete_uc),
    )


async def make_active_deal_with_offer(ucs, init_id, partner_id, iron_amount=10,
                                      iron_price=100, ducats=600):
    """Сценарий: сделка + ресурс у инициатора + эскроу дукатов у партнёра."""
    from mining_app.apps.items.deals.schemas import (
        DealCreateSchema,
        DealCurrencyOfferUpdateSchema,
        DealResourceOfferUpdateSchema,
    )

    ucs.char_client.online_ids = {init_id, partner_id}
    await seed_resource(ucs.session, slug="iron", price=iron_price)
    await seed_character_resource(ucs.session, init_id, "iron", 100)

    deal = await ucs.create_uc(user(init_id), DealCreateSchema(
        partner_character_id=partner_id, location_slug=DEAL_LOCATION))
    await ucs.add_res_uc(deal.id, "iron", user(init_id),
                         DealResourceOfferUpdateSchema(amount=iron_amount))
    if ducats:
        await ucs.set_ducats_uc(deal.id, user(partner_id), DealCurrencyOfferUpdateSchema(
            amount=Decimal(str(ducats)), operation_id=uuid_mod.uuid4()))
    return deal


_TABLE_LIST = ", ".join(f'"{name}"' for name in Base.metadata.tables)


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(engine):
    """Чистая сессия БД на каждый тест (таблицы усечены)."""
    async with engine.connect() as conn:
        await conn.execute(sa.text(f"TRUNCATE TABLE {_TABLE_LIST} RESTART IDENTITY CASCADE"))
        await conn.commit()

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session
