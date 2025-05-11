# =========================================================
# ASSIST_KEY: このファイルは【core/constants.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは “共通定数 & 共有ユーティリティ” として、
#   PDCA サイクル間で参照される定数・環境設定を一元管理します。
#
# 【主な役割】
#   - 共有ディレクトリ (artifacts/・pdca_data/) の基準パスを定義
#   - 評価指標・ファイル命名規約などの定数を提供
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core/common/io_utils.py          … パス組み立てに使用
#       ・core/check/check_executor.py     … メトリクス名を参照
#   - 外部設定 :
#       ・.env (PDCA_ROOT / ARTIFACT_ROOT の上書き可)
#
# 【ルール遵守】
#   1) グローバル変数直書き禁止  → Path や値は必ずここ経由
#   2) 破壊的変更時は docs/ARCH.md を更新
#   3) ハードコード発見時は # FIXME: ハードコード で残す
# ---------------------------------------------------------
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# ----------------------------------------------------------------------
# 1) ルートディレクトリ (環境変数で上書き可)
# ----------------------------------------------------------------------
PROJECT_ROOT: Final[Path] = Path(os.getenv("PDCA_ROOT", ".")).resolve()

# 保存物 (Parquet) 置き場
ARTIFACT_ROOT: Final[Path] = Path(
    os.getenv("ARTIFACT_ROOT", PROJECT_ROOT / "artifacts")
).resolve()

# Plan / Do / Check の補助 JSON 等
PDCA_META_ROOT: Final[Path] = Path(
    os.getenv("PDCA_META_ROOT", PROJECT_ROOT / "pdca_data")
).resolve()

# ----------------------------------------------------------------------
# 2) 共通ファイル名 / サブフォルダ規約
# ----------------------------------------------------------------------
PREDICTION_FILENAME: Final[str] = "predictions.parquet"
META_FILENAME: Final[str] = "meta.json"

# ----------------------------------------------------------------------
# 3) 評価指標 (Check フェーズで公式サポートするもの)
# ----------------------------------------------------------------------
SUPPORTED_METRICS: Final[tuple[str, ...]] = (
    "mape",
    "rmse",
    "r2",
)

# ----------------------------------------------------------------------
# 4) Parquet オプション
# ----------------------------------------------------------------------
DEFAULT_PARQUET_COMPRESSION: Final[str] = "zstd"  # FIXME: ハードコード
PARQUET_VERSION: Final[str] = "2.6"


# ----------------------------------------------------------------------
# 5) 便利関数
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    プロジェクト起動時に artifacts/ と pdca_data/ を作成するヘルパー。
    UI / API どこから呼んでも安全 (存在チェック付き)。
    """
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    PDCA_META_ROOT.mkdir(parents=True, exist_ok=True)


# 公開シンボル
__all__ = [
    "PROJECT_ROOT",
    "ARTIFACT_ROOT",
    "PDCA_META_ROOT",
    "PREDICTION_FILENAME",
    "META_FILENAME",
    "SUPPORTED_METRICS",
    "DEFAULT_PARQUET_COMPRESSION",
    "PARQUET_VERSION",
    "ensure_directories",
]
