# infra/db/migrations/env.py  ─── UTF-8 (BOM なし) で保存
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

# ── ❶ 環境変数 > INI の順で DSN を決定
dsn = os.getenv("DATABASE_URL") or os.getenv("PG_DSN")
if dsn:
    config.set_main_option("sqlalchemy.url", dsn)

# ── ❷ ログ設定
fileConfig(config.config_file_name, disable_existing_loggers=False, encoding="utf-8")

# ここでアプリの MetaData を import しても OK
target_metadata = None

# ── オフライン / オンライン
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
