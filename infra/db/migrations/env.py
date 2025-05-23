"""
Alembic run-script

1. Alembic Config から logging を初期化
2. DATABASE_URL → PG_DSN → alembic.ini の順に DSN を注入
3. オフライン / オンライン両モードに対応してマイグレーション実行
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ────────────────────────────
# 1) Alembic Config オブジェクト
# ────────────────────────────
config = context.config

# ────────────────────────────
# 2) 環境変数で DSN を上書き
#    DATABASE_URL > PG_DSN > alembic.ini
# ────────────────────────────
dsn = os.getenv("DATABASE_URL") or os.getenv("PG_DSN")
if dsn:
    config.set_main_option("sqlalchemy.url", dsn)

# ────────────────────────────
# 3) Logging 初期化
# ────────────────────────────
fileConfig(
    config.config_file_name,
    disable_existing_loggers=False,
    encoding="utf-8",
)

# モデルの MetaData を使わない場合は None のままで OK
target_metadata = None

# ---------------------------------------------------------------------------
# 以下、Alembic テンプレートそのまま
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
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
