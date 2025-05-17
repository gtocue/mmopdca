# =========================================================
# ASSIST_KEY: ...  ← 見出しはそのまま残しています
# =========================================================

import os
import yaml
import logging

from mmopdca_sdk import ApiClient, Configuration         # ← 変更なし
from mmopdca_sdk.api.plan_api import PlanApi
from mmopdca_sdk.exceptions import ApiException          # ← ★ 追加：正しい例外クラス

# ───────── ログ設定 ─────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────── 環境変数 ─────────
MMOP_BASE_URL = os.getenv("MMOP_BASE_URL", "http://localhost:8001")  # ★ 8001 をデフォルトに
MMOP_API_KEY  = os.getenv("MMOP_API_KEY",  "YOUR_API_KEY_HERE")      # FIXME: 外部設定へ

# ───────── API クライアント ─────────
config = Configuration(
    host=MMOP_BASE_URL,
    api_key={"x-api-key": MMOP_API_KEY}
)
client = ApiClient(configuration=config)
api    = PlanApi(client)


def main() -> None:
    # ───────── YAML 読み込み ─────────
    try:
        with open("plan.yaml", "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        logger.info("Loaded plan specification from plan.yaml")
    except FileNotFoundError:
        logger.warning("plan.yaml not found, using inline spec example")
        spec = {
            "symbol": "AAPL",
            "start":  "2025-05-01",
            "end":    "2025-06-01",
        }

    # ───────── Pydantic モデル変換 ─────────
    try:
        body = PlanCreateRequest(**spec)
    except Exception as e:
        logger.error(f"Invalid plan spec: {e}")
        return

    # ───────── API 呼び出し ─────────
    try:
        response = api.create_plan_plan_post(body)
        logger.info(f"✅ Run started successfully: run_id={response.run_id}")
    except ApiException as e:                      # ★ 修正
        logger.error("❌ API Exception occurred:")
        logger.error(f"  Status Code:   {e.status}")
        logger.error(f"  Response Body: {e.body}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
