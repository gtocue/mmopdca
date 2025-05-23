# infra/db/migrations/env.py
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

# ← この 3 行だけで十分
dsn = os.getenv("DATABASE_URL") or os.getenv("PG_DSN")
if dsn:
    config.set_main_option("sqlalchemy.url", dsn)

fileConfig(config.config_file_name, disable_existing_loggers=False, encoding="utf-8")
target_metadata = None
# ── 以下はテンプレそのまま ──
def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
