# =========================================================
# ASSIST_KEY: 【tests/api/test_plan_dsl_api.py】
# =========================================================
#
# /plan-dsl/ エンドポイント E2E テスト
#   * multipart/form-data (file=...) で POST する
# ---------------------------------------------------------
from pathlib import Path

SAMPLE_BYTES = Path("samples/plan_mvp.yaml").read_bytes()


def test_create_and_get_plan(client):
    # Create (multipart/form-data)
    res = client.post(
        "/plan-dsl/",
        files={"file": ("plan_mvp.yaml", SAMPLE_BYTES, "application/x-yaml")},
    )
    assert res.status_code == 201
    body = res.json()
    plan_id = body["id"]
    assert body["data"]["universe"] == ["MSFT"]

    # Get
    res2 = client.get(f"/plan-dsl/{plan_id}")
    assert res2.status_code == 200
    assert res2.json()["id"] == plan_id
