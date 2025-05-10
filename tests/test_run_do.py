#!/usr/bin/env python3
# test_run_do.py
# ──────────────────────────────────────────────────────────────
# Do フェーズのコア実行関数 run_do が同期でどれだけ時間を要するかを計測するテストスクリプト
# プロセス停止や Celery を介さず、直接 run_do を呼び出して実行速度と戻り値を確認できます
# ──────────────────────────────────────────────────────────────
import time

from core.do.coredo_executor import run_do


def main():
    params = {
        "symbol": "AAPL",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "indicators": [],
        "run_no": 1,
        "run_tag": "",
    }
    print("Starting run_do...")
    start = time.time()
    try:
        result = run_do("plan_dummy", params)
        elapsed = time.time() - start
        print(f"run_do returned: {result}")
        print(f"Elapsed time: {elapsed:.2f} seconds")
    except Exception as e:
        elapsed = time.time() - start
        print(f"run_do raised exception after {elapsed:.2f}s: {e}")

if __name__ == "__main__":
    main()
