from importlib import metadata
from typing import Dict, Type

from common_core.adapters.base import BaseAdapter

_ENTRY_POINT = "mmopdca_adapters"

_cache: Dict[str, Type[BaseAdapter]] = {}


def _discover() -> None:
    """entry_points 経由でプラグインを収集してキャッシュ"""
    eps = metadata.entry_points(group=_ENTRY_POINT)
    for ep in eps:
        try:
            cls = ep.load()
            if issubclass(cls, BaseAdapter):
                _cache[ep.name] = cls
        except Exception:  # pragma: no cover
            # ロード失敗は無視して続行
            pass


def get(name: str) -> Type[BaseAdapter]:
    """プラグイン名から Adapter クラスを取得"""
    if not _cache:  # 初回だけ遅延ロード
        _discover()
    return _cache[name]
