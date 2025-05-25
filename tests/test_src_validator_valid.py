# tests/test_src_validator_valid.py
import pytest
from src.validator.src_validator_core import validate_dsl

@pytest.fixture
def valid_dsl():
    return {
        "version": "plan_v1",
        "baseline": {"horizon_days": 5, "strategy": "mean"},
        "row_count": 100,
        "feature_blocks": [{"name": "MovingAverage", "params": {"window": 10}}]
    }

def test_validate_success(valid_dsl):
    plan = validate_dsl(valid_dsl)
    assert plan.baseline.horizon_days == 5
