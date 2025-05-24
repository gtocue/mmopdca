try:
    from pydantic import ConfigDict, field_validator
except ImportError:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = dict  # type: ignore[misc]
    from pydantic import validator as field_validator  # type: ignore

__all__ = ["ConfigDict", "field_validator"]

