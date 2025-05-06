# =========================================================
# ASSIST_KEY: cli/predict_cli.py
# =========================================================
#
# 【概要】
#   mmopdca の “予測専用” CLI エントリポイント。
#   コマンド:  `python -m cli.predict_cli predict MSFT -h "30,90,365"`
#
# 【主な役割】
#   - Typer で引数を解析し GarchProphetPredictor を呼び出す
#   - JSON で標準出力へ結果をエコー
#
# 【連携先・依存関係】
#   - core/prediction/garch_prophet.GarchProphetPredictor
#   - tests/test_predict.py（e2e テスト用）
#
# 【ルール遵守】
#   1) 機能削除・breaking change は事前相談
#   2) 標準出力以外への副作用（ファイル書込み等）は行わない
# ---------------------------------------------------------

from __future__ import annotations

import json
from typing import List

import typer

from core.prediction.garch_prophet import GarchProphetPredictor

app = typer.Typer(
    add_completion=False,
    help="mmopdca 予測 CLI: 複数ホライズンの p5/p50/p95/vector を取得",
)


@app.command()
def predict(
    ticker: str = typer.Argument(..., help="ティッカー例: MSFT"),
    horizon: str = typer.Option(
        "30,90,365",
        "--horizon",
        "-h",
        help="カンマ区切りの日数 (例: 30,90,365)",
    ),
):
    """
    指定ティッカー / ホライズンの予測を JSON で出力します。
    """
    try:
        horizons: List[int] = [int(h) for h in horizon.split(",") if h.strip()]
    except ValueError:
        typer.secho("❌ horizon は整数カンマ区切りで渡してください", fg=typer.colors.RED)
        raise typer.Exit(1)

    predictor = GarchProphetPredictor(ticker)
    result = predictor.predict(horizons)
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()
