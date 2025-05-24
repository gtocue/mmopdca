from pathlib import Path

import pytest

# ← 修正: クラスごと import
from core.dsl.validator import DSLValidator, ValidationError


@pytest.fixture(scope="module")
def validator() -> DSLValidator:
    """DSLValidator instance pointing to local schema dir."""
    schemas_dir = Path(__file__).parents[2] / "core" / "dsl" / "schemas"
    return DSLValidator(schemas_dir)


def test_baseline_default_horizon(validator: DSLValidator) -> None:
    plan = {"baseline": {"lookback_days": 30, "strategy": "mean"}}
    # メソッド呼び出しに変更
    validator.validate_plan(plan)


def test_baseline_invalid_strategy(validator: DSLValidator) -> None:
    plan = {"baseline": {"lookback_days": 7, "strategy": "avg"}}
    with pytest.raises(ValueError):  # ValidationError は内部で ValueError 包装
        validator.validate_plan(plan)
