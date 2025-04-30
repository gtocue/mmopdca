# =========================================================
# ASSIST_KEY: 【core/dsl/loader.py】
# =========================================================
#
# 【概要】
#   PlanLoader ― Plan-DSL ファイル (*plan.yaml / .json*) を読み込み、
#   defaults ＋ markets 変換 ＋ JSON-Schema 検証を行ったうえで
#   “純粋 dict” を返却するファサード。
#
# 【主な機能・責務】
#   - .env 変数で DSL_ROOT / DEFAULTS_DIR / SCHEMAS_DIR を上書き可
#   - defaults/*.json を deep-merge して欠損フィールドを補完
#   - defaults/markets_*_defaults.json を束ねて名称→ティッカー変換
#   - schemas/*.json があれば fastjsonschema でセクション単位バリデート
#   - legacy_dict() で旧システム互換 dict をワンステップで射影
#
# 【連携先・依存関係】
#   - core/dsl/store/fs_store.py      : ファイル I/O
#   - core/dsl/validator.py           : Schema + pydantic 検証
#   - core/do/coredo_executor.py 等   : 下流ロジック
#
# 【ルール遵守】
#   1) グローバル変数直書き禁止（環境変数か pdca_data 経由）
#   2) “ハルシネーション禁止” – 不確かな仕様は TODO コメントで残す
#   3) logging を使用し print() は使わない
# ---------------------------------------------------------

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

from .store.fs_store import FSStore
from .validator import DSLValidator

try:
    import jsonschema  # type: ignore
except ModuleNotFoundError:  # バリデーションを強制しない
    jsonschema = None  # type: ignore

logger = logging.getLogger(__name__)

# =====================================================================
# ディレクトリ設定 (.env で上書き可)
# =====================================================================
DSL_ROOT = Path(
    os.getenv("DSL_ROOT", Path(__file__).parent / "defaults")
).expanduser().resolve()

DEFAULTS_DIR = Path(
    os.getenv("DEFAULTS_DIR", DSL_ROOT / "defaults")
).expanduser().resolve()

SCHEMAS_DIR = Path(
    os.getenv("SCHEMAS_DIR", DSL_ROOT / "schemas")
).expanduser().resolve()

_STORE = FSStore(DSL_ROOT)
_VALIDATOR = DSLValidator(SCHEMAS_DIR)


# =====================================================================
# public API
# =====================================================================
class PlanLoader:
    """
    Plan-DSL をロードし defaults マージ → markets 置換 →
    スキーマ検証までを 1shot で実行する Facade。
    """

    def __init__(self, validate: bool = True) -> None:
        if validate and jsonschema is None:
            logger.warning("jsonschema が無いため Schema 検証をスキップします")
        self.validate_flag = validate and jsonschema is not None

        # ★ 1 回だけロードしてキャッシュ
        self._defaults: Dict[str, Any] = _load_defaults()
        self._market_map: dict[str, str] = _load_market_mapping()

    # -----------------------------------------------------------------
    # main
    # -----------------------------------------------------------------
    def load(self, plan_path: str | Path) -> Dict[str, Any]:
        """Plan ファイル → dict (defaults マージ済み) を返す"""
        logger.info("Loading plan: %s", plan_path)

        plan_dict = _load_yaml_or_json(plan_path)
        merged = _deep_merge(self._defaults, plan_dict)
        merged = _resolve_market_names(merged, self._market_map)

        # ---- optional fastjsonschema ----
        if self.validate_flag:
            _validate_by_schemas(merged)

        return merged

    # -----------------------------------------------------------------
    # legacy compatibility hook
    # -----------------------------------------------------------------
    def legacy_dict(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存コードが期待する “平坦な dict” へ射影。
        *当面そのまま返す*。後方互換が壊れたらここで調整。
        """
        # TODO: 旧フィールド名の rename が必要になればここで実装
        return plan


# =====================================================================
# internal helpers
# =====================================================================
def _load_yaml_or_json(path: str | Path) -> Dict[str, Any]:
    """拡張子を自動判定して YAML / JSON を dict 化"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    txt = _STORE.read_text(p)
    if p.suffix.lower() in (".yml", ".yaml"):
        return yaml.safe_load(txt) or {}
    return json.loads(txt)


def _load_defaults() -> Dict[str, Any]:
    """defaults ディレクトリ配下 *.json を再帰的に読み込んで deep-merge"""
    merged: Dict[str, Any] = {}
    for fp in DEFAULTS_DIR.rglob("*.json"):
        try:
            merged = _deep_merge(merged, json.loads(fp.read_text()))
        except json.JSONDecodeError as exc:  # noqa: TRY003
            logger.error("defaults JSON パース失敗: %s – %s", fp, exc)
    logger.debug("defaults files loaded: %d", len(list(DEFAULTS_DIR.rglob('*.json'))))
    return merged


def _load_market_mapping() -> dict[str, str]:
    """markets/*_defaults.json を統合し 名称→ティッカー dict を返す"""
    mapping: dict[str, str] = {}
    for fp in (DEFAULTS_DIR / "markets").glob("*_defaults.json"):
        mapping.update(json.loads(fp.read_text()))
    return mapping


def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """辞書を再帰マージ（src 優先）"""
    out = dst.copy()
    for k, v in src.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve_market_names(plan: Dict[str, Any], name2ticker: dict[str, str]) -> Dict[str, Any]:
    """
    data.universe 内で “正式名称” をティッカーへ置換する。
    名称が未登録ならそのまま返す。
    """
    universe = plan.get("data", {}).get("universe")
    if isinstance(universe, list):
        plan["data"]["universe"] = [name2ticker.get(x, x) for x in universe]
    return plan


def _validate_by_schemas(plan: Dict[str, Any]) -> None:
    """
    schemas/*.json が存在すれば該当セクションのみ fastjsonschema で検証。
    (例) preprocessing_schema.json → plan['preprocessing'] または plan['materials']['preprocessing']
    """
    for schema_fp in SCHEMAS_DIR.glob("*_schema.json"):
        section_key = schema_fp.stem.replace("_schema", "")
        target = plan.get(section_key) or plan.get("materials", {}).get(section_key)
        if target is None:
            continue  # セクションが無ければ検証しない

        try:
            _VALIDATOR.validate_json(target, schema_fp.name)
        except ValueError as exc:  # DSLValidator が ValueError を送出
            raise RuntimeError(f"[SchemaError] {schema_fp.name}: {exc}") from None


# ---------------------------------------------------------------------
# CLI quick-test:
#   python -m core.dsl.loader path/to/plan.yaml
# ---------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import sys
    import pprint

    _path = sys.argv[1] if len(sys.argv) > 1 else "samples/plan.yaml"
    loader = PlanLoader(validate=False)
    pprint.pp(loader.load(_path), depth=3, compact=True)
