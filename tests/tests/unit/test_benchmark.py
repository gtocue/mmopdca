# tests/unit/test_benchmark.py
import pytest
from core.do.coredo_executor import run_do

@pytest.mark.benchmark(group="run_do")
def test_run_do_speed(benchmark):
    params = {
        "symbol": "AAPL",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "indicators": [],
        "run_no": 1,
        "run_tag": "",
    }
    # ベンチマーク対象として計測
    result = benchmark(lambda: run_do("plan_dummy", params))
    # 戻り値の型やキーの存在は必ずチェック
    assert isinstance(result, dict)
    assert "some_expected_key" in result
