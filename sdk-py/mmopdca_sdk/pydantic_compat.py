import pydantic

if pydantic.VERSION.startswith("1"):
    # pydantic v1 compatibility
    def ConfigDict(**kwargs):
        return dict(**kwargs)
    from pydantic import validator as field_validator  # type: ignore
else:  # pragma: no cover - pydantic v2
    from pydantic import ConfigDict, field_validator

__all__ = ["ConfigDict", "field_validator"]
