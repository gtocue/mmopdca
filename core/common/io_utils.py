# =========================================================
# ASSIST_KEY: このファイルは【core/common/io_utils.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは “I/O ユーティリティ” として、
#   Parquet / JSON の読み書き・パス解決ロジックを提供します。
#
# 【主な役割】
#   - artifacts/ 以下の Parquet ファイル入出力
#   - pdca_data/ 以下の meta.json 読み書き
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core/do/do_executor.py       … save_predictions()
#       ・core/check/check_executor.py … load_predictions(), load_meta()
#   - 外部設定 :
#       ・core/constants.py            … ルートパス・ファイル名利用
#
# 【ルール遵守】
#   1) pandas / polars のどちらかが import 可能な方を自動選択
#   2) 例外は “上位で握らずここで握る” (IOError → RuntimeError 変換)
#   3) CLI デバッグは logging.debug() を使用し print 禁止
# ---------------------------------------------------------
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from core.constants import (
    ARTIFACT_ROOT,
    PDCA_META_ROOT,
    PREDICTION_FILENAME,
    META_FILENAME,
    DEFAULT_PARQUET_COMPRESSION,
)

# --------------------------------------------------
# データフレームライブラリ (polars > pandas 優先)
# --------------------------------------------------
try:
    import polars as pl  # type: ignore

    _DF_LIB = "polars"
except ModuleNotFoundError:  # pragma: no cover
    import pandas as pd  # type: ignore

    _DF_LIB = "pandas"

logger = logging.getLogger(__name__)


# --------------------------------------------------
# パス組み立てヘルパー
# --------------------------------------------------
def _artifact_dir(plan_id: str, run_id: str) -> Path:
    return ARTIFACT_ROOT / plan_id / run_id


def artifact_path(plan_id: str, run_id: str) -> Path:
    """
    予測 Parquet の絶対パスを返す。
    """
    return _artifact_dir(plan_id, run_id) / PREDICTION_FILENAME


def meta_path(plan_id: str, run_id: str) -> Path:
    """
    meta.json の絶対パスを返す。
    """
    return PDCA_META_ROOT / plan_id / run_id / META_FILENAME


# --------------------------------------------------
# Parquet 読み書き
# --------------------------------------------------
def save_predictions(df: Any, plan_id: str, run_id: str) -> str:
    """
    予測結果 DataFrame を Parquet 保存し、その **URI 文字列** を返す。

    Returns
    -------
    str
        `artifacts/{plan_id}/{run_id}/predictions.parquet`
        の絶対パス文字列
    """
    path = artifact_path(plan_id, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    if _DF_LIB == "polars":
        assert isinstance(df, pl.DataFrame)
        df.write_parquet(
            path,
            compression=DEFAULT_PARQUET_COMPRESSION,
            statistics=True,
        )
    else:  # pandas
        assert "pandas" in str(type(df)), "pandas.DataFrame expected"
        df.to_parquet(
            path,
            compression=DEFAULT_PARQUET_COMPRESSION,
            index=False,
        )

    logger.debug("Predictions saved: %s", path)
    return str(path.resolve())


def load_predictions(plan_id: str, run_id: str) -> Any:
    """
    Parquet をロードして DataFrame を返却。
    """
    path = artifact_path(plan_id, run_id)
    if not path.exists():
        raise RuntimeError(f"Prediction file not found: {path}")

    if _DF_LIB == "polars":
        return pl.read_parquet(path)
    else:
        return pd.read_parquet(path)  # type: ignore


# --------------------------------------------------
# Meta JSON 読み書き
# --------------------------------------------------
def save_meta(meta: dict[str, Any], plan_id: str, run_id: str) -> str:
    """
    meta.json を保存（dict → JSON）。戻り値は保存先 URI。
    """
    path = meta_path(plan_id, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    logger.debug("Meta saved: %s", path)
    return str(path.resolve())


def load_meta(plan_id: str, run_id: str) -> dict[str, Any]:
    """
    meta.json をロードして dict を返す。
    """
    path = meta_path(plan_id, run_id)
    if not path.exists():
        raise RuntimeError(f"Meta file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# 公開シンボル
__all__ = [
    "artifact_path",
    "meta_path",
    "save_predictions",
    "load_predictions",
    "save_meta",
    "load_meta",
]
