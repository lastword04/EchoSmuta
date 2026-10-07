from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from economy_app.core.db import Base
from economy_app.settings import settings

# Импорт моделей для autogenerate (регистрируют таблицы в Base.metadata)
import economy_app.apps.pawn_shop.models  # noqa: F401,E402
import economy_app.apps.tavern.models  # noqa: F401,E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Устанавливаем URL из настроек (синхронный)
config.set_main_option("sqlalchemy.url", settings.db.sync_dsn)

# Interpret the config file for Python logging.
# Мы пропускаем fileConfig, чтобы избежать ошибок с отсутствующими секциями.
# Вместо этого можно настроить логгер вручную, если нужно, но для миграций это не обязательно.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        settings.db.sync_dsn,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
