# =========================================================
# ASSIST_KEY: このファイルは【tests/schemas/test_artifact.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   PredictionRecord / PredictionArtifact の
#   “モデル整合性 & JSON ラウンドトリップ” テスト。
# ---------------------------------------------------------
from datetime import datetime

from core.schemas.artifact_schemas import PredictionRecord, PredictionArtifact


def test_artifact_roundtrip() -> None:
    record = PredictionRecord(
        symbol="MSFT",
        ts=datetime.utcnow(),
        horizon=5,
        y_true=320.0,
        y_pred=321.2,
        model_id="dummy_model",
    )

    artifact = PredictionArtifact(records=[record])

    # JSON → Model round-trip
    payload = artifact.model_dump_json()
    loaded = PredictionArtifact.model_validate_json(payload)

    assert loaded.records[0].symbol == "MSFT"
    assert loaded.records[0].y_pred == 321.2
