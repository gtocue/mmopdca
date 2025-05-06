# =========================================================
# ASSIST_KEY: api/routers/predict_api.py
# =========================================================
#
# 【概要】
#   /predict/{ticker} エンドポイントを提供する FastAPI ルータ。
#   クエリ string `horizon=30,90,365` を受け取り、
#   JSON で予測結果を返す。
#
# 【連携先・依存関係】
#   - core/prediction/garch_prophet.GarchProphetPredictor
#   - api/main_api.py で app.include_router() される想定
#
# 【注意】
#   - 助言回避のため、推奨語や買いシグナルは返さない。
# ---------------------------------------------------------

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from core.prediction.garch_prophet import GarchProphetPredictor

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get("/{ticker}", summary="複数ホライズン予測")
def predict(
    ticker: str,
    horizon: str = Query("30,90,365", description="カンマ区切りの日数"),
):
    try:
        horizons: List[int] = [int(h) for h in horizon.split(",") if h.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="horizon は整数カンマ区切り")

    predictor = GarchProphetPredictor(ticker)
    try:
        result = predictor.predict(horizons)
    except Exception as e:  # NOTE: 例外→HTTP 500
        raise HTTPException(status_code=500, detail=str(e))

    return {"ticker": ticker.upper(), "horizons": result}
