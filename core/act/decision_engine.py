# =========================================================
# ASSIST_KEY: このファイルは【core/act/decision_engine.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   decision_engine ― CheckResult を評価して ActDecision を返す
#
# 【主なロジック】
#   - r2 が threshold 以上 → noop
#   - r2 が閾値未満        → retrain を指示
#
# ---------------------------------------------------------

from __future__ import annotations

import uuid
from datetime import datetime

from core.schemas.check_schemas import CheckResult
from core.schemas.act_schemas import ActDecision


# NOTE: 閾値は CheckResult.report 内の threshold をそのまま使う。
#       なければデフォルト 0.8
_DEFAULT_THRESHOLD = 0.80


def decide(check: CheckResult) -> ActDecision:
    """CheckResult を読み取り、取るべき action を決定する MVP 実装"""

    r2 = float(check.report.get("r2", 0.0))
    threshold = float(check.report.get("threshold", _DEFAULT_THRESHOLD))

    if r2 >= threshold:
        action = "noop"
        reason = "accuracy within threshold"
    else:
        action = "retrain"
        reason = f"low accuracy (r2={r2:.3f} < {threshold:.2f})"

    return ActDecision(
        id=f"act-{uuid.uuid4().hex[:8]}",
        check_id=check.id,
        decided_at=datetime.utcnow(),
        action=action,
        reason=reason,
    )
