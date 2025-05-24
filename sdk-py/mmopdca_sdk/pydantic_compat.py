try:
    from pydantic import ConfigDict, field_validator
except ImportError:  # pragma: no cover - support pydantic v1
    ConfigDict = dict  # type: ignore
    from pydantic import validator as field_validator  # type: ignore

__all__ = ["ConfigDict", "field_validator"]
