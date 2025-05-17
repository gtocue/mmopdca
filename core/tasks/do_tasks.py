# core/tasks/do_tasks.py
# =========================================================
# 【概要】
#   Do フェーズの Celery タスク実装
#   - Do タスクの実行ステータス管理と結果の永続化
#
# 【主な役割】
#   - run_do_task: Do フェーズの非同期実行
#   - ステータス遷移（PENDING → RUNNING → DONE/FAILED）
#   - 結果またはエラー詳細の格納
#
# 【連携先・依存関係】
#   - core.do.coredo_executor.run_do
#   - core.repository.factory.get_repo
#   - core.schemas.do_schemas.DoStatus
#
# 【ルール遵守】
#   1) Pydantic 型名・リポジトリ key は統一
#   2) datetime は UTC ISO8601 形式
#   3) SQLiteRepository のメソッド（delete/create）を利用し upsert を実現
# =========================================================

import logging
from datetime import datetime, timezone

from core.celery_app import celery_app  # ← 自前の Celery インスタンスをインポート
from core.do.coredo_executor import run_do
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoStatus

logger = logging.getLogger(__name__)
_do_repo = get_repo("do")


def _upsert(do_id: str, rec: dict) -> None:
    """
    指定した do_id のレコードを削除し、
    新規作成することで upsert を実現するユーティリティ。
    """
    try:
        _do_repo.delete(do_id)
    except Exception:
        # 存在しない場合は無視
        pass
    _do_repo.create(do_id, rec)


@celery_app.task(
    name="core.tasks.do_tasks.run_do_task",
    acks_late=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def run_do_task(do_id: str, plan_id: str, params: dict) -> None:
    """
    Do フェーズを実行し、リポジトリにステータスと結果を記録する Celery タスク。

    Args:
        do_id (str): Do フェーズの一意 ID ("do-xxxxxx")
        plan_id (str): 元となる Plan の ID ("plan-xxxxxx")
        params (dict): run_do 関数に渡すパラメータ
    """
    # 1) RUNNING にステータス更新
    rec = _do_repo.get(do_id) or {}
    rec.update(
        {
            "do_id": do_id,
            "plan_id": plan_id,
            "status": DoStatus.RUNNING,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _upsert(do_id, rec)

    try:
        # 2) 実際の分析処理を呼び出し
        result = run_do(plan_id, params)

        # 3) DONE と結果を保存
        rec = _do_repo.get(do_id) or {}
        rec.update(
            {
                "status": DoStatus.DONE,
                "result": result,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _upsert(do_id, rec)

    except Exception as e:
        # 4) FAILED とエラー詳細を保存
        logger.error("Do task failed: %s", e, exc_info=True)
        rec = _do_repo.get(do_id) or {}
        rec.update(
            {
                "status": DoStatus.FAILED,
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _upsert(do_id, rec)
        # Celery にも例外を伝搬させて失敗として扱わせる
        raise
