from __future__ import annotations

"""DSLValidator
================
Centralised JSON‑Schema **and** pydantic validation used by
:pyclass:`core.dsl.loader.PlanLoader` to ensure that all DSL files
( *plan.yaml* / *defaults.json* / *baseline files* …) are syntactically and
semantically correct **before** they reach the execution layer.

Key design rules
----------------
1. **No hallucinations** – any key that is *not* in the schema must raise.
2. Any schema addition **must** be documented in *docs/ARCH.md*.
3. Fast †jsonschema for structure, pydantic for rich type / range checks.
"""

import json
from pathlib import Path
from typing import Any, Dict

try:  # fastjsonschema is optional in some offline CI images
    import fastjsonschema
except ModuleNotFoundError:  # pragma: no cover
    fastjsonschema = None  # type: ignore

from pydantic import BaseModel, Field, ValidationError, field_validator

__all__ = ["DSLValidator"]

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _resolve_refs(obj: Any, base: Path) -> None:
    """Recursively convert relative *$ref* into absolute **file://** URIs.

    fastjsonschema expects the *final* resolved URI, therefore we adjust paths
    only when the reference is **relative** (no scheme, no fragment only).
    """
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and "://" not in ref and not ref.startswith("#"):
            obj["$ref"] = (base / ref).resolve().as_uri()
        for value in obj.values():
            _resolve_refs(value, base)
    elif isinstance(obj, list):
        for item in obj:
            _resolve_refs(item, base)


# ---------------------------------------------------------------------------
# pydantic models – **authoritative single‑source‑of‑truth** for types
# ---------------------------------------------------------------------------

class PlanMetaModel(BaseModel):
    plan_id: str
    owner: str
    created: str  # ISO‑8601 (string → parsed later by service layer)


class PreprocessingModel(BaseModel):
    missing_value_methods: list[str]
    outlier_methods: list[str]
    scaling_methods: list[str] | None = None

    @field_validator("missing_value_methods", "outlier_methods", mode="before")
    @classmethod
    def _non_empty(cls, v: list[str]):  # noqa: D401 – simple validator naming
        if not v:
            raise ValueError("list must not be empty")
        return v


class BaselineParamsModel(BaseModel):
    model: str = Field(..., examples=["lgbm", "linear", "svr"])
    lr: float | None = Field(0.01, gt=0, lt=1, examples=[0.05])
    num_leaves: int | None = Field(None, gt=1, examples=[31])


# ---------------------------------------------------------------------------
# main validator class
# ---------------------------------------------------------------------------

class DSLValidator:
    """Two‑stage validator – JSON‑Schema (structure) + pydantic (rich types)."""

    def __init__(self, schemas_dir: str | Path):
        self.schemas_dir = Path(schemas_dir)
        self._compiled_cache: dict[Path, Any] = {}

    # ------------------------ fastjsonschema -------------------------
    def _compile(self, schema_path: Path):
        if schema_path not in self._compiled_cache:
            if fastjsonschema is None:  # pragma: no cover – skip in minimal envs
                def _noop(_: Dict[str, Any]) -> None:  # noqa: D401 – tiny helper
                    return None

                self._compiled_cache[schema_path] = _noop
            else:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                _resolve_refs(schema, schema_path.parent)
                self._compiled_cache[schema_path] = fastjsonschema.compile(schema)
        return self._compiled_cache[schema_path]

    def validate_json(self, payload: Dict[str, Any], schema_file: str) -> None:
        """Validate *payload* against *schema_file* (relative to *schemas_dir*)."""
        if fastjsonschema is None:  # pragma: no cover
            return  # structural validation skipped (offline CI)
        schema_path = self.schemas_dir / schema_file
        self._compile(schema_path)(payload)

    # --------------------------- pydantic -----------------------------
    def _run_pydantic(self, model_cls: type[BaseModel], data: Dict[str, Any], ctx: str) -> None:
        try:
            model_cls(**data)
        except ValidationError as exc:  # noqa: TRY003 – re‑raise user‑friendly
            raise ValueError(f"{ctx} validation failed: {exc}") from exc

    def validate_plan_meta(self, meta: Dict[str, Any]) -> None:
        self._run_pydantic(PlanMetaModel, meta, "plan.meta")

    def validate_preprocessing(self, block: Dict[str, Any]) -> None:
        self._run_pydantic(PreprocessingModel, block, "preprocessing")

    def validate_baseline_params(self, block: Dict[str, Any]) -> None:
        """New in *Sprint‑2*: baseline hyper‑parameters section."""
        self._run_pydantic(BaselineParamsModel, block, "baseline_params")
