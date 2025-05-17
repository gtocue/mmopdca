"""Schema package exports."""
from importlib import import_module
from typing import List

__all__: List[str] = []

for _name in ("plan_schemas", "do_schemas", "prediction"):
    try:
        _module = import_module(f"{__name__}.{_name}")
    except ModuleNotFoundError:
        continue
    for _sym in getattr(_module, "__all__", ()):  # skip modules without __all__
        globals()[_sym] = getattr(_module, _sym)
        __all__.append(_sym)

del _module, _name, _sym