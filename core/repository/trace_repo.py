"""
core/repository/trace_repo.py
────────────────────────────
シンプルな JSON Lines 形式で Trace を保管／ストリームするリポジトリ。
ストレージを後で S3 / DynamoDB に差し替えられるよう抽象化してある。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Generator, Iterable, Iterator, List

TRACE_ROOT = Path("pdca_data/trace")  # ローカル保管先


class TraceRepo:
    """Trace (event) を run_id 単位で append / stream する I/F"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or TRACE_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------- #
    # Low-level helpers
    # --------------------------------------------------------------------- #

    def _file(self, run_id: str) -> Path:
        return self.root / f"{run_id}.jsonl"

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def put(self, run_id: str, event: Dict) -> None:
        """
        1 イベントを追記保存。event は JSON シリアライズ可能 dict。
        """
        f = self._file(run_id)
        with f.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")

    def stream(self, run_id: str) -> Iterator[Dict]:
        """
        イベントを順番どおりに yield するジェネレータ。
        """
        f = self._file(run_id)
        if not f.exists():
            return iter([])  # 空イテレータ

        with f.open("r", encoding="utf-8") as fp:
            for line in fp:
                if line.strip():
                    yield json.loads(line)

    # 便利メソッド --------------------------------------------------------- #

    def exists(self, run_id: str) -> bool:
        return self._file(run_id).exists()

    def delete(self, run_id: str) -> None:
        """
        単体テスト用: Trace ファイルを削除。
        """
        f = self._file(run_id)
        if f.exists():
            f.unlink()
