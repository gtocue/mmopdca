"""Minimal pandas stub used for unit tests.

This file provides only the small subset of functionality required by the
tests in this repository.  The real :mod:`pandas` package is intentionally not
used in CI to keep the environment lightweight.  However, some third party
libraries (e.g. ``sklearn``) expect the ``pandas`` module to expose a
``__version__`` attribute.  Without it they fail to import, which caused the
CI run to break.  To emulate the real package just enough, we expose a simple
``DataFrame`` class and define ``__version__``.
"""

__version__ = "0.0"


class DataFrame(list):
    def __init__(self, data):
        keys = list(data.keys())
        rows = list(zip(*data.values()))
        super().__init__([{k: v[i] for k, v in data.items()} for i in range(len(rows))])
        self._columns = keys

    @property
    def columns(self):
        return self._columns

    def __len__(self):
        return super().__len__()
        