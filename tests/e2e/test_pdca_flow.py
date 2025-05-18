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
from core.common.io_utils import save_predictions, save_meta, load_predictions
from core.schemas.meta_schemas import MetaInfo, MetricSpec
from core.check.check_executor import CheckExecutor
from core.constants import ensure_directories

# …（ダミー DataFrame 作成部分は省略せずそのまま）…

def test_pdca_min_cycle(tmp_path) -> None:
    ensure_directories()
    plan_id = "plan_" + uuid.uuid4().hex[:6]
    run_id = "run_" + uuid.uuid4().hex[:6]

    df = _make_dummy_df()
    save_predictions(df, plan_id, run_id)

    meta = MetaInfo(
        plan_id=plan_id,
        run_id=run_id,
        train_start=date(2023, 1, 1),
        train_end=date(2024, 1, 1),
        predict_horizon=5,
        metrics=[MetricSpec(name="mape", threshold=10.0)],
    )
    save_meta(meta.model_dump(mode="json"), plan_id, run_id)

    result = CheckExecutor.run(plan_id, run_id)
    assert result.do_id == run_id
    assert isinstance(result.report.passed, bool)

    df_loaded = load_predictions(plan_id, run_id)
    assert len(df_loaded) == 3
