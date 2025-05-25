# core/eval/__init__.py
"""
Evaluation utilities package.

`evaluate` を直接 import できるように再エクスポートする。
"""

from .metrics import evaluate  # ← ここで公開
__all__: list[str] = ["evaluate"]
