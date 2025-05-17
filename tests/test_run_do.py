#!/usr/bin/env python3
# test_run_do.py
# ──────────────────────────────────────────────────────────────
# Do フェーズの同期実行時間を計測するユーティリティ。
# Celery を介さず core.do.coredo_executor.run_do を直接呼び出す。
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import time
from pathlib import Path
import sys

# プロジェクト直下でスクリプト単体実行しても import できるように PATH を追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.do.coredo_executor import run_do  # noqa: E402  pylint: disable=wrong-import-position


def main() -> None:
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
        print(f"✅ run_do returned: {result}")
        print(f"⏱  Elapsed time : {elapsed:.2f} s")
    except Exception as exc:  # noqa: BLE001
        elapsed = time.time() - start
        print(f"❌ run_do raised after {elapsed:.2f} s: {exc}")


if __name__ == "__main__":
    main()
