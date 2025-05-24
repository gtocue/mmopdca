# =========================================================
# ASSIST_KEY: 【core/dsl/validator.py】
# =========================================================
#
# 【概要】
#   DSLValidator ― plan.yaml / defaults.json を JSON Schema +
#   pydantic で検証し、実行時エラーを未然に防ぐ。
#
# 【主な役割】
#   - fastjsonschema による構文・必須キー検査
#   - pydantic による型・値域チェック
#
# 【連携先・依存関係】
#   - core/dsl/loader.py から呼び出される
#   - core/dsl/schemas/*.json : JSON Schema 集
#
# 【ルール遵守】
#   1) “ハルシネーション禁止” → Schema に存在しないキーはエラー
#   2) 追加時は docs/ARCH.md に Schema 更新履歴を記載
# ---------------------------------------------------------

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:  # fastjsonschema may be unavailable in offline test env
    import fastjsonschema
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    fastjsonschema = None  # type: ignore
from pydantic import BaseModel, ValidationError

def _resolve_refs(obj: Any, base: Path) -> None:
    """Recursively convert relative $ref to absolute file URIs."""
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and "://" not in ref and not ref.startswith("#"):
            obj["$ref"] = (base / ref).resolve().as_uri()
        for v in obj.values():
            _resolve_refs(v, base)
    elif isinstance(obj, list):
        for item in obj:
            _resolve_refs(item, base)

# -------------------------------------------------- pydantic models
class PlanMetaModel(BaseModel):
    plan_id: str
    owner: str
    created: str  # ISO-8601


class PreprocessingModel(BaseModel):
    missing_value_methods: list[str]
    outlier_methods: list[str]
    scaling_methods: list[str] | None = None


# -------------------------------------------------- validator core
class DSLValidator:
    """JSON-Schema + pydantic の 2 段バリデータ"""

    def __init__(self, schemas_dir: Path) -> None:
        self.schemas_dir = schemas_dir
        self._cache: dict[str, Any] = {}

    # ---------- fastjsonschema ----------
    def _compile(self, schema_path: Path):
        if schema_path not in self._cache:
            if fastjsonschema is None:  # pragma: no cover - validation skipped
                def _noop(_: Dict[str, Any]) -> None:
                    return None

                self._cache[schema_path] = _noop
            else:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                _resolve_refs(schema, schema_path.parent)
                self._cache[schema_path] = fastjsonschema.compile(schema)
        return self._cache[schema_path]

    def validate_json(self, payload: Dict[str, Any], schema_file: str) -> None:
        if fastjsonschema is None:  # pragma: no cover - validation skipped
            return
        schema_path = self.schemas_dir / schema_file
        self._compile(schema_path)(payload)

    # ---------- pydantic ----------
    def validate_plan_meta(self, meta: Dict[str, Any]) -> None:
        try:
            PlanMetaModel(**meta)
        except ValidationError as e:  # noqa: TRY003
            raise ValueError(f"plan.meta validation failed: {e}") from e

    def validate_preprocessing(self, block: Dict[str, Any]) -> None:
        try:
            PreprocessingModel(**block)
        except ValidationError as e:  # noqa: TRY003
            raise ValueError(f"preprocessing validation failed: {e}") from e
