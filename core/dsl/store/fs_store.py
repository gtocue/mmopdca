# =========================================================
# ASSIST_KEY: 【core/dsl/store/fs_store.py】
# =========================================================
#
# 【概要】
#   FSStore ― DSL ディレクトリをローカル FS 経由で操作する Driver。
#
# 【主な役割】
#   - DSL_ROOT 配下の JSON / YAML などを読み書き
#   - glob で一覧取得（Marketplace/S3Store 追加時も同 API を共有）
#
# 【連携先・依存関係】
#   - core/dsl/loader.py : Store Factory から呼び出される
#   - .env               : DSL_ROOT / DEFAULTS_DIR などのパス上書き
#
# 【ルール遵守】
#   1) ログは logging に統一（print 禁止）
#   2) 型安全 & pathlib ベースで OS 依存を排除
#   3) pdca_data[...] への直接書込みは行わない
# ---------------------------------------------------------

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class FSStore:
    """File-System ベースの DSL Store"""

    def __init__(self, root: str | Path) -> None:
        self.root: Path = Path(root).expanduser().resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"DSL root not found: {self.root}")
        logger.debug("FSStore initialised at %s", self.root)

    # -----------------------------------------------------------------
    # internal helpers
    # -----------------------------------------------------------------
    def _abs(self, path: str | Path) -> Path:
        """root 相対 → 絶対 Path へ正規化"""
        path = Path(path)
        return path if path.is_absolute() else self.root / path

    # -----------------------------------------------------------------
    # public API
    # -----------------------------------------------------------------
    def list(self, pattern: str = "**/*") -> List[Path]:
        """glob でマッチする *ファイル* を列挙"""
        files = [p for p in self.root.glob(pattern) if p.is_file()]
        logger.debug("FSStore.list(%s) -> %d files", pattern, len(files))
        return files

    def exists(self, path: str | Path) -> bool:
        return self._abs(path).exists()

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        abspath = self._abs(path)
        logger.debug("read_text: %s", abspath)
        return abspath.read_text(encoding=encoding)
