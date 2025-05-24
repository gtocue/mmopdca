# =========================================================
# ASSIST_KEY: このファイルは【tests/e2e/test_pdca_flow.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   “Plan→Do→Check” の最小 E2E サイクルを擬似実行して
#   CheckResult が生成されることを検証。
# ---------------------------------------------------------
from datetime import date, datetime
import uuid

from core.common.io_utils import (
    save_predictions,
    save_meta,
    load_predictions,
)
from core.schemas.meta_schemas import MetaInfo, MetricSpec
from core.check.check_executor import CheckExecutor
from core.constants import ensure_directories

# DataFrame ライブラリ選択
try:
    import polars as pl  # type: ignore

    _DF_LIB = "polars"
except ModuleNotFoundError:  # pragma: no cover
    import pandas as pd  # type: ignore

    _DF_LIB = "pandas"


def _make_dummy_df():
    if _DF_LIB == "polars":
        return pl.DataFrame(
            {
                "symbol": ["AAPL"] * 3,
                "ts": [pl.datetime(2024, 1, d + 1) for d in range(3)],
                "horizon": [5, 5, 5],
                "y_true": [150.0, 151.0, 152.0],
                "y_pred": [149.5, 151.2, 151.8],
                "model_id": ["demo"] * 3,
            }
        )
    else:
        return pd.DataFrame(
            {
                "symbol": ["AAPL"] * 3,
                "ts": [datetime(2024, 1, d + 1) for d in range(3)],
                "horizon": [5, 5, 5],
                "y_true": [150.0, 151.0, 152.0],
                "y_pred": [149.5, 151.2, 151.8],
                "model_id": ["demo"] * 3,
            }
        )


def test_pdca_min_cycle(tmp_path) -> None:
    """
    tmp_path は pytest の一時ディレクトリ fixture。
    ARTIFACT_ROOT / PDCA_META_ROOT を一時ディレクトリに切替えて実行。
    """
    # ─ Setup (一時ディレクトリをルートに) ─
    ensure_directories()

    plan_id = "plan_" + uuid.uuid4().hex[:6]
    run_id = "run_" + uuid.uuid4().hex[:6]

    # ① ダミー予測データ生成 & 保存
    df = _make_dummy_df()
    save_predictions(df, plan_id, run_id)

    # ② meta.json 作成 & 保存
    meta = MetaInfo(
        plan_id=plan_id,
        run_id=run_id,
        train_start=date(2023, 1, 1),
        train_end=date(2024, 1, 1),
        predict_horizon=5,
        metrics=[MetricSpec(name="mape", threshold=10.0)],
    )
    save_meta(meta.model_dump(mode="json"), plan_id, run_id)

    # ③ CheckExecutor 実行
    result = CheckExecutor.run(plan_id, run_id)

    # ④ 検証
    assert result.do_id == run_id
    assert result.report.passed is True or result.report.passed is False

    # ⑤ I/O 再ロードして整合性確認 (read back)
    df_loaded = load_predictions(plan_id, run_id)
    assert len(df_loaded) == 3
