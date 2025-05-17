# =========================================================
# ASSIST_KEY: examples/quickstart.py
# =========================================================
import os
import yaml
import logging

from mmopdca_sdk import ApiClient, Configuration
from mmopdca_sdk.api.plan_api import PlanApi
from mmopdca_sdk.models.plan_create_request import PlanCreateRequest
from mmopdca_sdk.exceptions import ApiException  # 正しい例外

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MMOP_BASE_URL = os.getenv("MMOP_BASE_URL", "http://localhost:8001")
MMOP_API_KEY = os.getenv("MMOP_API_KEY", "")

config = Configuration(host=MMOP_BASE_URL, api_key={"x-api-key": MMOP_API_KEY})
client = ApiClient(configuration=config)
api = PlanApi(client)


def main() -> None:
    # plan.yaml があれば読む
    try:
        with open("plan.yaml", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        logger.info("Loaded plan.yaml")
    except FileNotFoundError:
        logger.warning("plan.yaml not found – using inline sample")
        spec = {"symbol": "AAPL", "start": "2025-05-01", "end": "2025-06-01"}

    try:
        body = PlanCreateRequest(**spec)
    except Exception as exc:
        logger.error("Invalid spec: %s", exc)
        return

    try:
        resp = api.create_plan_plan_post(body)
        logger.info("✅ Run started: run_id=%s", resp.run_id)
    except ApiException as exc:
        logger.error("API error %s: %s", exc.status, exc.body)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)


if __name__ == "__main__":
    main()
