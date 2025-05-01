# =========================================================
# ASSIST_KEY: core/tasks/do_tasks.py
# =========================================================
#
# 【概要】
#   Celery タスク – Plan を解析する “Do” ジョブの実装。
#
# 【主な役割】
#   - Plan→Do の非同期実行
#   - core.do.coredo_executor.run_do() を呼び出し
#
# 【連携先・依存関係】
#   - core.models.do.DoStatus
#   - core.repository.do_pg_impl.DoRepository
#   - core.repository.postgres_impl.PostgresRepository   (plan 読み出し)
#   - core.dsl.loader.PlanLoader                         (defaults 反映)
#   - core.do.coredo_executor.run_do                     (既存ビジネスロジック)
#
# 【ルール遵守】
#   1) ハードコード値には FIXME/TODO をつける
#   2) print() ではなく logging を使用
# ---------------------------------------------------------
from __future__ import annotations

import logging

from celery import shared_task, Task

from core.dsl.loader import PlanLoader
from core.models.do import DoStatus
from core.repository.do_pg_impl import DoRepository
from core.repository.postgres_impl import PostgresRepository
from core.do.coredo_executor import run_do as legacy_run_do

# ------------------------------------------------------------------
# Repository DI
# ------------------------------------------------------------------
_plan_repo = PostgresRepository(table="plan")  # FIXME: schema 名を .env へ
_do_repo   = DoRepository()
_loader    = PlanLoader(validate=False)        # Plan 登録時に検証済み想定

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Celery Task
# ------------------------------------------------------------------
@shared_task(bind=True, name="run_do", acks_late=True, max_retries=3)
def run_do(self: Task, do_id: str, plan_id: str) -> None:  # noqa: D401
    """
    Celery entry-point: Plan を解析し Do 結果を保存する。

    Parameters
    ----------
    do_id   : str
        Do 実行レコードの ID（予め UI / API で作成済）
    plan_id : str
        実行対象 Plan の ID
    """
    # -- 前準備 -----------------------------------------------------
    do_doc = _do_repo.get(do_id)
    if do_doc is None:
        logger.error("[Do] record %s not found – abort", do_id)
        return

    do_doc["status"] = DoStatus.RUNNING
    _do_repo.create(do_id, do_doc)

    try:
        # 1) Plan 取得
        plan_raw = _plan_repo.get(plan_id)
        if plan_raw is None:
            raise ValueError(f"plan '{plan_id}' not found")

        # 2) defaults マージ・market 置換をもう一度適用
        plan_merged = _loader.load_dict(plan_raw)
        legacy_dict = _loader.legacy_dict(plan_merged)

        # 3) 既存 Executor 呼び出し
        logger.info("[Do] start executor for %s", plan_id)
        result = legacy_run_do(legacy_dict)       # <-- 既存ビジネスロジック
        logger.info("[Do] finished %s", plan_id)

        # 4) 成功結果保存
        do_doc.update(
            status=DoStatus.DONE,
            result=result,
        )
        _do_repo.create(do_id, do_doc)

    except Exception as exc:  # noqa: BLE001
        logger.exception("[Do] %s failed: %s", do_id, exc)
        do_doc.update(
            status=DoStatus.FAILED,
            result={"error": str(exc)},
        )
        _do_repo.create(do_id, do_doc)
        # Celery にリトライさせる（最大 max_retries）
        raise self.retry(exc=exc, countdown=30)  # FIXME: バックオフ時間を設定値化
