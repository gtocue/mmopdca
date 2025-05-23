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
        
    def __getitem__(self, key):
        return [row.get(key) for row in self]

    # --------------------------------------------------
    # Minimal persistence helpers used in tests
    # --------------------------------------------------
    def to_pickle(self, path):
        import json
        def _convert(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([{k: _convert(v) for k, v in row.items()} for row in self], f)

    def to_parquet(self, path, compression=None, index=True):  # pragma: no cover - simplified
        self.to_pickle(path)


def read_pickle(path):
    import json
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not data:
        return DataFrame({})
    keys = list(data[0].keys())
    cols = {k: [row.get(k) for row in data] for k in keys}
    return DataFrame(cols)


def read_parquet(path):  # pragma: no cover - simplified
    return read_pickle(path)