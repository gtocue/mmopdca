# =========================================================
# ASSIST_KEY: core/models/do.py
# =========================================================
#
# 【概要】
#   Do ユニット – Plan を実行する “Do ジョブ” のドメインモデルを提供。
#
# 【主な役割】
#   - Do オブジェクトのスキーマ定義（Pydantic）
#   - ステータス管理用 Enum 相当クラスを内包
#
# 【連携先・依存関係】
#   - core/tasks/do_tasks.py : Celery タスクで利用
#   - api/routers/do_api.py  : FastAPI ルータのレスポンスモデル
#
# 【ルール遵守】
#   1) メイン銘柄は扱わない
#   2) 市場名 suffix 規則は対象外（Do はメタ情報のみ保持）
#   3) 本ファイル全体を返却
# ---------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DoStatus:  # NOTE: Enum ではなく文字列定数にして軽量化
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Do(BaseModel):
    """Do (= Plan を実際に解析するジョブ) のドメインモデル"""

    do_id: str
    plan_id: str
    status: Literal["queued", "running", "done", "failed"] = DoStatus.QUEUED
    result: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
