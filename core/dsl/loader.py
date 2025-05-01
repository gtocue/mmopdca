# =========================================================
# ASSIST_KEY: 【core/dsl/loader.py】
# =========================================================
#
# PlanLoader ― Plan DSL を読み込み
#   1. defaults deep-merge
#   2. market 名 → ティッカー置換
#   3. JSON-Schema + pydantic 検証（validate=True 時）
# した dict を返す Facade。
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
except ModuleNotFoundError:          # バリデーションを強制しない
    jsonschema = None                # type: ignore

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# ディレクトリ設定（.env で上書き可）
# ------------------------------------------------------------------
DSL_ROOT     = Path(os.getenv("DSL_ROOT", Path(__file__).parent)).resolve()
DEFAULTS_DIR = DSL_ROOT / "defaults"
SCHEMAS_DIR  = DSL_ROOT / "schemas"

_STORE     = FSStore(DSL_ROOT)
_VALIDATOR = DSLValidator(SCHEMAS_DIR)

# ==================================================================
# public  API
# ==================================================================
class PlanLoader:
    """
    Plan-DSL をロードして共通前処理を施す Facade。
      * load(path)   : ファイル経由
      * load_dict(d) : すでに dict 化された DSL
    """

    def __init__(self, validate: bool = True) -> None:
        if validate and jsonschema is None:
            logger.warning("jsonschema が無いため Schema 検証をスキップします")
        self._validate = validate and jsonschema is not None

        # キャッシュ
        self._defaults: Dict[str, Any]   = _load_defaults()
        self._market_map: dict[str, str] = _load_market_mapping()

    # -------------------------------------------------------------
    # ★ dict を直接受け取る
    # -------------------------------------------------------------
    def load_dict(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        merged = _deep_merge(self._defaults, plan)
        merged = _resolve_market_names(merged, self._market_map)

        if self._validate:
            _validate_by_schemas(merged)

        return merged

    # -------------------------------------------------------------
    # ファイル経由
    # -------------------------------------------------------------
    def load(self, plan_path: str | Path) -> Dict[str, Any]:
        logger.info("Loading plan: %s", plan_path)
        plan_dict = _load_yaml_or_json(plan_path)
        return self.load_dict(plan_dict)          # ← 共通処理へ集約

    # -------------------------------------------------------------
    # legacy 互換フック
    # -------------------------------------------------------------
    def legacy_dict(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        旧 Plan API が要求するフィールド（symbol / start / end）を
        Plan DSL から補完して返す。
        """
        legacy = dict(plan)  # シャローコピー

        # symbol = universe の先頭
        legacy.setdefault(
            "symbol",
            (plan.get("data", {}).get("universe") or [""])[0],
        )
        # start / end = train_start / train_end
        dates = plan.get("dates", {})
        legacy.setdefault("start", dates.get("train_start"))
        legacy.setdefault("end",   dates.get("train_end"))

        return legacy


# ==================================================================
# internal helpers
# ==================================================================
def _load_yaml_or_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(p)
    txt = _STORE.read_text(p)
    return yaml.safe_load(txt) if p.suffix.lower() in (".yml", ".yaml") else json.loads(txt)


def _load_defaults() -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for fp in DEFAULTS_DIR.rglob("*.json"):
        try:
            merged = _deep_merge(
                merged,
                json.loads(fp.read_text(encoding="utf-8")),
            )
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("defaults JSON スキップ: %s – %s", fp, exc)
    return merged


def _load_market_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for fp in (DEFAULTS_DIR / "markets").glob("*_defaults.json"):
        try:
            mapping.update(json.loads(fp.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("market defaults スキップ: %s – %s", fp, exc)
    return mapping


def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    out = dst.copy()
    for k, v in src.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve_market_names(plan: Dict[str, Any], mp: dict[str, str]) -> Dict[str, Any]:
    uni = plan.get("data", {}).get("universe")
    if isinstance(uni, list):
        plan["data"]["universe"] = [mp.get(x, x) for x in uni]
    return plan


def _validate_by_schemas(plan: Dict[str, Any]) -> None:
    for schema_fp in SCHEMAS_DIR.glob("*_schema.json"):
        section = schema_fp.stem.replace("_schema", "")
        target = plan.get(section) or plan.get("materials", {}).get(section)
        if target is not None:
            _VALIDATOR.validate_json(target, schema_fp.name)


# -----------------------------------------------------------------
# CLI quick-test:
#   poetry run python -m core.dsl.loader samples/plan_mvp.yaml
# -----------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import sys, pprint
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("samples/plan_mvp.yaml")
    pprint.pp(PlanLoader(validate=False).load(path), depth=2, compact=True)
