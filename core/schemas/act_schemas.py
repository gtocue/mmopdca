# =========================================================
# ASSIST_KEY: このファイルは【core/schemas/act_schemas.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは ActDecision スキーマを提供します。
#   Check フェーズの評価結果を読み取り、
#   「Deploy するか / Retrain するか / 何もしないか」など
#   Act フェーズで取るアクションを表現します。
#
# 【主な役割】
#   - ActDecision  : /act API の I/O ＆ 永続化フォーマット
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・api/routers/act_api.py      … Act REST ハンドラ
#       ・core/schemas/check_schemas.py (予定) … CheckResult
#   - 外部設定 :
#       ・なし（定数は各 Router 側で持つ）
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は "Close_Nikkei_225" / "Open_SP500" のように suffix で区別
#   3) **全体コード** を返却（スニペット不可）
#   4) 本ヘッダーは必ず残すこと
#   5) 機能削除・breaking change は要相談（原則 “追加” のみ）
#   6) pdca_data[...] に統一（本ユニットは直接アクセスしない）
#
# 【注意事項】
#   - 型安全重視 (Pydantic v2)・ハルシネーション厳禁
#   - TODO: action は Enum 化・reason は i18n を検討
# ---------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ActAction(str, Enum):
    noop = "noop"
    retrain = "retrain"
    alert = "alert"


class ActDecision(BaseModel):
    id: str = Field(..., description="act-xxxx 一意 ID")
    check_id: str = Field(..., description="紐づく Check ID")
    decided_at: datetime = Field(..., description="UTC ISO8601")
    action: ActAction
    reason: str = Field(..., description="意思決定根拠 (人間可読)")
