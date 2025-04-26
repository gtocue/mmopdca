# =========================================================
# ASSIST_KEY: このファイルは【infra/db/migrations/env.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   Alembic エントリポイント。`alembic upgrade head` などの実行時に呼ばれ、
#   - 環境変数 PG_DSN から DSN を注入
#   - “モデル定義なし”でも JSON スキーマをマイグレート出来るよう設定
#
# 【主な役割】
#   - run_migrations_offline / online で DB と接続して DDL を流す
#
# 【連携先・依存関係】
#   - .alembic.ini           … sqlalchemy.url はダミーで可
#   - 環境変数 PG_DSN       … postgresql://user:pass@host:port/db
#
# 【ルール遵守】
#   1) DSN は必ず **環境変数側が優先**（CI・本番で差し替えやすく）
#   2) ORM を使わないため `target_metadata=None` で autogenerate する
#   3) logging は fileConfig をそのまま利用
#
# ----------------------------------------------------------

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ──────────────────────────────────────────────────────────
# 基本設定
# ──────────────────────────────────────────────────────────
config = context.config  # alembic.ini をパースした Config オブジェクト

# ======== DSN を環境変数で上書き ========
# .ini の `sqlalchemy.url` はダミーで良い
dsn_env = os.getenv("PG_DSN")
if dsn_env:
    # psycopg3 用にドライバ接頭辞を補正
    if dsn_env.startswith("postgresql://"):
        dsn_env = dsn_env.replace("postgresql://", "postgresql+psycopg://", 1)
    config.set_main_option("sqlalchemy.url", dsn_env)

# ======== ロギング ========
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ======== メタデータ（未使用） ========
# JSONB ストレージのみなので ORM 定義は持たない
target_metadata = None

# ──────────────────────────────────────────────────────────
# マイグレーション実行関数
# ──────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Engine を生成せずに SQL を標準出力へ吐き出すモード
    (`alembic upgrade --sql …` 用)
    """
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
    """
    通常モード: DB へ直接 DDL を適用
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# ──────────────────────────────────────────────────────────
# エントリポイント
# ──────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
