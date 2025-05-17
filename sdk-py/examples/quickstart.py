# =========================================================
# ASSIST_KEY: このファイルは【examples/quickstart.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは Quickstart Example として、
#   Python SDK を使った API 呼び出しの最小構成サンプルを提供します。
#
# 【主な役割】
#   - 環境変数からベース URL / API キーのロード
#   - YAML ファイルまたは直接指定による PlanCreateRequest の構築
#   - Plan API の呼び出しとエラーハンドリング
#
# 【連携先・依存関係】
#   - SDK クライアント: mmopdca_sdk.ApiClient, Configuration
#   - API クラス:    mmopdca_sdk.api.plan_api.PlanApi
#   - モデル:        mmopdca_sdk.models.plan_create_request.PlanCreateRequest
#   - 外部設定:      plan.yaml (cli/mmop-init により生成)
#
# 【ルール遵守】
#   1) ハードコード値発見時は # FIXME: ハードコード を追加
#   2) logging を使い、print は最小限に留める
#   3) 型安全重視 (Pydantic モデルを利用)
#   4) ファイル冒頭に本ヘッダーを残す
#   5) 全体コードを返却
#   6) 環境変数直書き禁止 (# FIXME: 外部設定へ)
#
# ---------------------------------------------------------

import os
import yaml
import logging

from mmopdca_sdk import ApiClient, Configuration
from mmopdca_sdk.api.plan_api import PlanApi
from mmopdca_sdk.models.plan_create_request import PlanCreateRequest

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数ロード
MMOP_BASE_URL = os.getenv("MMOP_BASE_URL", "http://localhost:8000")  # FIXME: 外部設定へ
MMOP_API_KEY  = os.getenv("MMOP_API_KEY",  "YOUR_API_KEY_HERE")     # FIXME: 外部設定へ

# API クライアント初期化
config = Configuration(
    host=MMOP_BASE_URL,
    api_key={"x-api-key": MMOP_API_KEY}
)
client = ApiClient(configuration=config)
api    = PlanApi(client)


def main():
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
            "end":    "2025-06-01"
        }

    # ───────── Pydantic モデルへの変換 ─────────
    try:
        body = PlanCreateRequest(**spec)
    except Exception as e:
        logger.error(f"Invalid plan spec: {e}")
        return

    # ───────── API 呼び出し & エラーハンドリング ─────────
    try:
        response = api.create_plan_plan_post(body)
        logger.info(f"✅ Run started successfully: run_id={response.run_id}")
    except client.ApiException as e:
        logger.error("❌ API Exception occurred:")
        logger.error(f"  Status Code:   {e.status}")
        logger.error(f"  Response Body: {e.body}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
