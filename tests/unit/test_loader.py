from pathlib import Path
import yaml
from core.dsl.loader import PlanLoader

SAMPLE_YAML = Path("samples/plan_mvp.yaml")


def test_loader_roundtrip():
    loader = PlanLoader(validate=True)
    plan_dict = yaml.safe_load(SAMPLE_YAML.read_text(encoding="utf-8"))
    plan = loader.load_dict(plan_dict)
    assert plan["data"]["universe"] == ["MSFT"]
    assert "indicators" in plan
