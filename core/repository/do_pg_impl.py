# =========================================================
# ASSIST_KEY: core/repository/do_pg_impl.py
# =========================================================
#
# 【概要】
#   DoRepository – Do 用 PostgreSQL(JSONB) リポジトリ。
#
# 【主な役割】
#   - Do オブジェクトを PostgreSQL に CRUD する
#   - 親クラス PostgresRepository の薄いラッパ
#
# 【連携先・依存関係】
#   - core/repository/postgres_impl.py : 共通 JSONB 実装
#   - api/routers/do_api.py            : CRUD API
#   - core/tasks/do_tasks.py           : Celery タスク
#
# 【ルール遵守】
#   1) pdca_data 以外のグローバル参照を持たない
#   2) breaking change が必要なら事前相談
# ---------------------------------------------------------

from __future__ import annotations

from core.repository.postgres_impl import PostgresRepository


class DoRepository(PostgresRepository):
    """Do テーブル専用の PostgreSQL Repository"""

    def __init__(self, schema: str = "public"):
        # NOTE: table 名は固定で "do"
        super().__init__(table="do", schema=schema)
        # 追加機能が出るまで親実装をそのまま利用
