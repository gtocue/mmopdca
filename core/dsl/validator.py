from __future__ import annotations

"""core/dsl/validator.py  —  DSL Validator

・JSON Schema で構文／必須キーを一次検査
・pydantic で型／値域を二次検査
・baseline セクションの厳格バリデーションを追加 (Sprint‑2)

変更履歴
──────────
2025‑05‑25  v1.2  Pydantic V2 スタイルへ移行
"""

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import fastjsonschema  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – optional dependency (CI offline)
    fastjsonschema = None  # type: ignore

from pydantic import BaseModel, Field, ValidationError
try:
    from pydantic import field_validator, model_validator  # type: ignore
except ImportError:  # pragma: no cover - Pydantic v1 fallback
    from pydantic import validator, root_validator  # type: ignore

    def field_validator(field: str, *, mode: str = "before"):
        pre = mode == "before"

        def decorator(fn):
            return validator(field, pre=pre, allow_reuse=True)(fn)  # type: ignore

        return decorator

    def model_validator(*, mode: str = "after"):
        pre = mode == "before"

        def decorator(fn):
            if pre:
                return root_validator(pre=True, allow_reuse=True)(fn)  # type: ignore

            def wrapper(cls, values):
                self = cls.construct(**values)
                result = fn(self)
                if isinstance(result, BaseModel):
                    return result.dict()
                return values

            return root_validator(pre=False, allow_reuse=True)(wrapper)  # type: ignore

        return decorator

# ---------------------------------------------------------------------------
# ヘルパー ― $ref の相対パスを絶対 URI へ解決
# ---------------------------------------------------------------------------

def _resolve_refs(obj: Any, base: Path) -> None:
    """fastjsonschema が読めるように $ref を絶対パスへ展開."""
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and "://" not in ref and not ref.startswith("#"):
            obj["$ref"] = (base / ref).resolve().as_uri()
        for v in obj.values():
            _resolve_refs(v, base)
    elif isinstance(obj, list):
        for item in obj:
            _resolve_refs(item, base)

# ---------------------------------------------------------------------------
# pydantic models — second‑stage validation
# ---------------------------------------------------------------------------

class PlanMetaModel(BaseModel):
    plan_id: str
    owner: str
    created: str  # ISO‑8601, 詳細フォーマットは JSON Schema 側でチェック


class PreprocessingModel(BaseModel):
    missing_value_methods: List[str]
    outlier_methods: List[str]
    scaling_methods: List[str] | None = None


class BaselineModel(BaseModel):
    lookback_days: int = Field(..., ge=1, le=365)
    horizon_days: int | None = Field(None, ge=1, le=90)
    strategy: str | None = Field("mean")

    @field_validator("strategy", mode="before")
    @classmethod
    def _strategy_validate(cls, v: str) -> str:
        allowed = {"mean", "median", "last"}
        if v not in allowed:
            raise ValueError(f"strategy must be one of {sorted(allowed)}")
        return v

    @model_validator(mode="after")
    def apply_defaults(self) -> "BaselineModel":
        """Model-level post processing after validation."""
        # lookback_days が None の場合は後続の自動補完ロジックで埋める想定
        return self

# ---------------------------------------------------------------------------
# DSLValidator 本体
# ---------------------------------------------------------------------------

class DSLValidator:
    """JSON Schema → pydantic の 2 段バリデータ"""

    def __init__(self, schemas_dir: Path) -> None:
        self.schemas_dir = schemas_dir
        self._schema_cache: Dict[Path, Any] = {}

    # ----- fastjsonschema --------------------------------------------------
    def _compile_schema(self, schema_path: Path):
        if schema_path not in self._schema_cache:
            if fastjsonschema is None:  # pragma: no cover — offline CI
                self._schema_cache[schema_path] = lambda _: None  # type: ignore[arg-type]
            else:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                _resolve_refs(schema, schema_path.parent)
                self._schema_cache[schema_path] = fastjsonschema.compile(schema)
        return self._schema_cache[schema_path]

    def validate_json(self, payload: Dict[str, Any], schema_file: str) -> None:
        """JSON Schema による一次検証."""
        if fastjsonschema is None:  # pragma: no cover
            return
        schema_path = self.schemas_dir / schema_file
        self._compile_schema(schema_path)(payload)

    # ----- pydantic second stage -------------------------------------------
    def validate_plan_meta(self, meta: Dict[str, Any]) -> None:
        try:
            PlanMetaModel(**meta)
        except ValidationError as e:
            raise ValueError(f"plan.meta validation failed: {e}") from e

    def validate_preprocessing(self, block: Dict[str, Any]) -> None:
        try:
            PreprocessingModel(**block)
        except ValidationError as e:
            raise ValueError(f"preprocessing validation failed: {e}") from e

    def validate_baseline(self, baseline: Dict[str, Any]) -> None:
        """Baseline パラメータ専用バリデーション."""
        try:
            BaselineModel(**baseline)
        except ValidationError as e:
            raise ValueError(f"baseline validation failed: {e}") from e

    # ----- entry point -----------------------------------------------------
    def validate_plan(self, plan: Dict[str, Any]) -> None:
        """plan 全体を検証 (JSON Schema 済み前提)."""
        if meta := plan.get("meta"):
            self.validate_plan_meta(meta)
        if prep := plan.get("preprocessing"):
            self.validate_preprocessing(prep)
        if baseline := plan.get("baseline"):
            self.validate_baseline(baseline)

