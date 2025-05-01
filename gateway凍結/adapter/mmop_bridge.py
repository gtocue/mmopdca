# =========================================================
# ASSIST_KEY: このファイルは【gateway/adapter/mmop_bridge.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは MmopBridge として、
#   “/forecast → Plan-DSL 生成 → mmopdca main-api 実行” の橋渡しを行います。
#
# 【主な役割】
#   - ForecastRequest → Jinja2 テンプレで plan.yaml を自動生成
#   - mmopdca `/plan-dsl`, `/do/{plan_id}` を HTTP 経由で呼び出し
#   - 実行完了までポーリングし予測結果を整形
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・gateway/api/router.py
#   - 外部設定 :
#       ・環境変数 `MMOP_API`  : http://main-api:8001 など
#       ・templates/*.yaml.j2  : DSL テンプレート
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は suffix 区別
#   3) **全体コード** を返却
#   4) ファイル冒頭ヘッダーを残す
#   5) breaking change は事前相談
#   6) グローバル変数直書き禁止（env / settings を経由）
# ---------------------------------------------------------

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import httpx
import jinja2
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Pydantic Schemas  (共有定義)
# ------------------------------------------------------------------


class ForecastRequest(BaseModel):
    target: str = Field(..., description="Ticker symbol e.g. 'SPY'")
    horizon: int = Field(5, gt=0, le=30, description="Prediction horizon (days)")
    context: dict[str, str] | None = Field(
        None, description="Additional context (risk_profile etc.)"
    )

    @validator("target")
    def upper_ticker(cls, v: str) -> str:  # noqa: N805
        return v.upper()


class ForecastResponse(BaseModel):
    forecast: float
    ci_lower: float
    ci_upper: float
    model_sha: str
    hash_link: str


# ------------------------------------------------------------------
# Constants / Env
# ------------------------------------------------------------------

MAIN_API: Final[str] = os.getenv("MMOP_API", "http://main-api:8001")
TEMPLATES_DIR: Final[Path] = (
    Path(__file__).parent.parent / "templates"
)  # gateway/templates
CLIENT_TIMEOUT: Final[float] = float(os.getenv("MMOP_GATEWAY_TIMEOUT", "300"))
POLL_INTERVAL: Final[int] = int(os.getenv("MMOP_GATEWAY_POLL_SEC", "3"))  # seconds

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
async def run_forecast(req: ForecastRequest) -> ForecastResponse:
    """
    1) DSL テンプレート描画
    2) mmopdca /plan-dsl 登録 → plan_id
    3) /do/{plan_id} キック → do_id
    4) /do/{do_id} をポーリング → DONE
    5) hash_link を付与して返却
    """
    plan_yaml = _render_plan_yaml(req)

    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        plan_id = await _register_plan(client, plan_yaml)
        do_id = await _kick_do(client, plan_id)
        result_block = await _poll_result(client, do_id)

    hash_link = _make_hash_link(plan_yaml, result_block["model_sha"])
    return ForecastResponse(**result_block, hash_link=hash_link)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------
def _render_plan_yaml(req: ForecastRequest) -> str:
    tpl = jinja_env.get_template("asset_management.yaml.j2")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rendered = tpl.render(target=req.target, horizon=req.horizon, now=now)
    logger.debug("plan.yaml rendered:\n%s", rendered)
    return rendered


async def _register_plan(client: httpx.AsyncClient, plan_yaml: str) -> str:
    headers = {"Content-Type": "application/x-yaml"}
    r = await client.post(f"{MAIN_API}/plan-dsl", content=plan_yaml, headers=headers)
    r.raise_for_status()
    plan_id: str = r.json()["plan_id"]
    logger.info("plan registered: %s", plan_id)
    return plan_id


async def _kick_do(client: httpx.AsyncClient, plan_id: str) -> str:
    r = await client.post(f"{MAIN_API}/do/{plan_id}")
    r.raise_for_status()
    do_id: str = r.json()["do_id"]
    logger.info("do started: %s", do_id)
    return do_id


async def _poll_result(client: httpx.AsyncClient, do_id: str) -> dict[str, float]:
    logger.info("polling do result: %s", do_id)
    while True:
        r = await client.get(f"{MAIN_API}/do/{do_id}")
        r.raise_for_status()
        payload = r.json()
        status_ = payload.get("status")
        if status_ not in ("PENDING", "RUNNING"):
            break
        await asyncio.sleep(POLL_INTERVAL)

    if status_ != "DONE":
        raise RuntimeError(f"run failed (status={status_})")

    return payload["result"]  # Expected keys: forecast, ci_lower, ci_upper, model_sha


def _make_hash_link(plan_yaml: str, model_sha: str) -> str:
    root = hashlib.sha256((plan_yaml + model_sha).encode()).hexdigest()
    # TODO: URL ベースは外部設定へ
    return f"https://worm/mmopdca/{root[:6]}/{root}.json"
