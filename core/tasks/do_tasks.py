# =========================================================
# ASSIST_KEY: core/tasks/do_tasks.py
# =========================================================
#
# 【概要】
#   Celery タスク – Plan を解析する “Do” ジョブの実装。
#
# 【主な役割】
#   - Plan→Do の非同期実行
#   - 実際の解析ロジックを呼び出すフックを提供（現状ダミー）
#
# 【連携先・依存関係】
#   - core/models/do.py          : ステータス管理
#   - core/repository/do_pg_impl : Do 保存
#   - core/repository/postgres_impl : Plan 読み出し
#
# 【ルール遵守】
#   1) ハードコード値には FIXME/TODO をつける
#   2) print() ではなく logging を使用
# ---------------------------------------------------------

from __future__ import annotations

import logging
import random
import time

from celery import shared_task

from core.models.do import DoStatus
from core.repository.do_pg_impl import DoRepository
from core.repository.postgres_impl import PostgresRepository

# Repositories ------------------------------------------------------
_do_repo = DoRepository()
_plan_repo = PostgresRepository(table="plan")  # FIXME: ハードコード – schema 外部設定化の余地

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="run_do")
def run_do(self, do_id: str, plan_id: str) -> None:  # noqa: D401
    """
    Plan に基づき解析を実行する Celery タスク。
    現状はダミーで数秒 sleep して成功させる。
    """
    do = _do_repo.get(do_id)
    if not do:  # NOTE: 初期レコードが消えていた場合
        logger.error("Do %s not found – abort", do_id)
        return

    # status -> running
    do["status"] = DoStatus.RUNNING
    _do_repo.create(do_id, do)

    try:
        plan = _plan_repo.get(plan_id)  # 解析対象の Plan
        # ----------------------------------------------------
        # TODO: 実際の解析ロジックに置き換える
        time.sleep(random.randint(2, 5))
        result = {"echo_plan": plan}
        # ----------------------------------------------------

        do["status"] = DoStatus.DONE
        do["result"] = result
        _do_repo.create(do_id, do)
        logger.info("Do %s finished", do_id)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Do %s failed: %s", do_id, exc)
        do["status"] = DoStatus.FAILED
        do["result"] = {"error": str(exc)}
        _do_repo.create(do_id, do)
        raise
