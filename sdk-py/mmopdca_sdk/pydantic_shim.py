try:
    from pydantic import validate_call
except ImportError:  # pragma: no cover - for pydantic v1
    from pydantic import validate_arguments as validate_call  # type: ignore

from pydantic import (
    Field,
    StrictFloat,
    StrictStr,
    StrictInt,
    StrictBytes,
)
try:
    from pydantic import ConfigDict, field_validator
except ImportError:  # pragma: no cover - for pydantic v1
    ConfigDict = dict  # type: ignore
    from pydantic.class_validators import validator as field_validator  # type: ignore

__all__ = [
    "validate_call",
    "Field",
    "StrictFloat",
    "StrictStr",
    "StrictInt",
    "StrictBytes",
    "ConfigDict",
    "field_validator",
]
