try:
    from pydantic import field_validator, ConfigDict
except ImportError:  # pragma: no cover - pydantic<2
    from pydantic import validator as field_validator  # type: ignore
    ConfigDict = dict  # type: ignore

__all__ = ["field_validator", "ConfigDict"]
