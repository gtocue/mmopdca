# =========================================================
# ASSIST_KEY: このファイルは【gateway/api/router.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは ForecastRouter として、
#   “AI-エージェント向け 予測 API (/forecast)” を実装／提供します。
#
# 【主な役割】
#   - POST /forecast : 予測要求を受け取り → Gateway-Adapter で DSL 生成 → mmopdca 実行結果を返却
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・gateway/adapter/mmop_bridge.py   … 実行ブリッジ
#       ・gateway/security/auth.py         … JWT / APIKey 検証
#   - 外部設定 :
#       ・環境変数 `MMOP_API` … mmopdca main-api の URL
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は suffix 区別（例: "Close_SP500"）
#   3) **全体コード** を返却
#   4) ファイル冒頭に必ず本ヘッダーを残すこと
#   5) 機能削除や breaking change は事前相談（原則 “追加” のみ）
#   6) pdca_data[...] キーに統一、グローバル変数直書き禁止
# ---------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

try:
    # security.auth はまだ空実装かもしれない—無ければ匿名許可
    from gateway.security.auth import verify_token  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    async def verify_token() -> None: ...
    # NOTE: 本番導入時に必ず実装すること（JWT / APIKey）
    logging.getLogger(__name__).warning("verify_token stub in use")

from gateway.adapter.mmop_bridge import (
    ForecastRequest,
    ForecastResponse,
    run_forecast,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forecast", tags=["forecast"])


# -----------------------------------------------------
# POST /forecast
# -----------------------------------------------------
@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ForecastResponse,
    summary="Predict asset price (horizon-days ahead)",
)
async def forecast_endpoint(
    req: ForecastRequest,
    _auth: Any = Depends(verify_token),
) -> ForecastResponse:
    """
    予測 API エントリポイント。

    Parameters
    ----------
    req : ForecastRequest
        target / horizon / context を含む JSON body
    _auth : Depends
        JWT / APIKey 検証（認証失敗時は 401 を自動返却）

    Returns
    -------
    ForecastResponse
        予測値・信頼区間・モデル署名・Hash-Link
    """
    try:
        response = await run_forecast(req)
        logger.info("forecast → target=%s horizon=%s", req.target, req.horizon)
        return response
    except Exception as exc:  # noqa: BLE001
        logger.exception("forecast failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"backend error: {exc}",
        ) from exc
