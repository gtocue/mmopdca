# =========================================================
# ASSIST_KEY: core/prediction/predictor_base.py
# =========================================================
#
# 【概要】
#   このユニットは PredictorBase として、
#   株価など時系列を「複数ホライズンでベクトル予測」する
#   モデル実装の共通インターフェースを定義します。
#
# 【主な役割】
#   - Horizon(⽇数) → p5 / p50 / p95 / vector を返す predict() を規定
#   - 実装クラスに共通のユーティリティ／型定義を提供
#
# 【連携先・依存関係】
#   - core/prediction/garch_prophet.py : 具体的なモデル実装
#   - api/routers/predict_api.py       : FastAPI ルータ
#   - cli/main.py                      : Typer CLI
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は "Close_Nikkei_225" / "Open_SP500" のように suffix で区別
#   3) **全体コード** を返却（スニペットではなくファイルの完成形）
#   4) ファイル冒頭に必ず本ヘッダーを残すこと
#   5) 機能削除や breaking change は事前相談（原則 “追加” のみ）
#   6) pdca_data[...] キーに統一し、グローバル変数直書き禁止
#
# 【注意事項】
#   - ハードコード値を見つけたら「# FIXME: ハードコード」を添付
#   - インターフェース変更時は docs/ARCH.md を必ず更新
#   - 型安全重視 (Pydantic / typing)・ハルシネーション厳禁
# ---------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, TypedDict


class HorizonResult(TypedDict):
    """単一ホライズンの予測結果型"""

    p5: float  # 下側 5 % 信頼区間
    p50: float  # 中央値（point forecast）
    p95: float  # 上側 95 % 信頼区間
    vector: float  # 現在値に対する上昇率 (p50/current - 1)


class PredictorBase(ABC):
    """
    すべての予測モデルが継承すべき抽象クラス。

    各実装は:
      1) __init__(ticker:str, **opts) で前準備
      2) predict([30,90,365]) → {30: {...}, 90: {...}, ...} を返す
    """

    def __init__(self, ticker: str, **options):
        self.ticker = ticker
        self.options = options  # TODO: 外部設定へ（モデル固有ハイパラ用）

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @abstractmethod
    def predict(self, horizons: List[int]) -> Dict[int, HorizonResult]:
        """
        指定 horizon(日) ごとに p5/p50/p95/vector を返す。
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _validate_horizons(self, horizons: List[int]) -> List[int]:
        """不正値・重複を排除し昇順ソートして返す"""
        cleaned = sorted(set(h for h in horizons if h > 0))
        if not cleaned:
            raise ValueError("horizons must contain at least one positive integer")
        return cleaned

    # NOTE: 追加の共通メソッド（例: yfinance ローダ、前処理など）が
    #       必要になったらここに実装する。
