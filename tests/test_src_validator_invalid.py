# tests/test_src_validator_invalid.py
import pytest
from src.validator.src_validator_core import validate_dsl
from pydantic import ValidationError

def test_missing_row_count():
    dsl = {"version": "plan_v1", "baseline": {"horizon_days": 5}, "feature_blocks": []}
    with pytest.raises(ValidationError):
        validate_dsl(dsl)
