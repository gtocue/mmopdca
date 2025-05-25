"""End‑to‑end minimal PDCA flow test (Plan → Do → Check).

This file belongs to **tests/e2e** and intentionally avoids any external
services.  All heavy‑weight parts (Celery, Redis …) are stubbed by
``tests/conftest.py`` so the suite can run on plain `pytest`.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

import pandas as pd
import pytest

from core.check.check_executor import CheckExecutor
from core.common.io_utils import load_predictions, save_meta, save_predictions
from core.constants import ensure_directories
from core.schemas.check_schemas import CheckReport
from core.schemas.meta_schemas import MetaInfo, MetricSpec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dummy_df() -> pd.DataFrame:
    """Return a tiny synthetic dataset that exercises the entire IO path."""

    return pd.DataFrame(
        {
            "symbol": ["TEST"] * 3,
            "ts": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3),
            ],
            "horizon": [1, 1, 1],
            "y_true": [1.0, 1.5, 2.0],
            "y_pred": [1.1, 1.4, 1.9],
            "model_id": ["dummy"] * 3,
        }
    )


# ---------------------------------------------------------------------------
# Test case
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_pdca_min_cycle(tmp_path) -> None:
    """Smoke‑test the *whole* PDCA pipeline with stubbed workers.

    - **Plan**  : nothing to persist – IDs are generated on the fly.
    - **Do**    : ``save_predictions`` writes a Parquet file the API expects.
    - **Check** : ``CheckExecutor`` reads the artefacts and produces a report.

    The assertions guarantee that:
    1. The check finished successfully.
    2. The dataset round‑trips through Parquet unchanged.
    """

    # ensure all artefact directories exist (tmp_path is ignored by codebase)
    ensure_directories()

    plan_id = f"plan_{uuid.uuid4().hex[:6]}"
    run_id = f"run_{uuid.uuid4().hex[:6]}"

    # 1) predictions.parquet
    df = _make_dummy_df()
    save_predictions(df, plan_id, run_id)

    # 2) meta.yaml
    meta = MetaInfo(
        plan_id=plan_id,
        run_id=run_id,
        train_start=date(2023, 1, 1),
        train_end=date(2024, 1, 1),
        predict_horizon=5,
        metrics=[MetricSpec(name="mape", threshold=10.0)],
    )
    save_meta(meta.model_dump(mode="json"), plan_id, run_id)

    # 3) run *Check* synchronously (see tests/conftest.py monkey‑patch)
    result = CheckExecutor.run(plan_id, run_id)

    assert result.do_id == run_id
    # ``report`` should be a ``CheckReport`` instance at this stage
    assert isinstance(result.report, CheckReport)
    assert result.report.passed is True

    # 4) ensure the Parquet round‑trip kept all rows
    df_loaded = load_predictions(plan_id, run_id)
    assert len(df_loaded) == 3
