import importlib
import pydantic

"""Backport a subset of Pydantic v2 APIs when running under v1.

Pydantic v1 does not provide ``field_validator`` or several ``BaseModel``
methods introduced in v2.  Some parts of the codebase rely on these newer
APIs, so when running with v1 we monkey patch compatible shims that forward to
their v1 equivalents.
"""

if pydantic.__version__.startswith("1."):
    from pydantic import BaseModel, validator

    def field_validator(*fields, mode="after"):
        """Shim for ``pydantic.v2.field_validator``.

        Parameters
        ----------
        *fields
            Field names to validate.
        mode : str, optional
            "before" or "after". Defaults to ``"after"``.
        """

        pre = mode == "before"

        def decorator(fn):
            return validator(*fields, pre=pre, allow_reuse=True)(fn)
        
        return decorator

    def model_validate(cls, data):
        """Mimic the ``model_validate`` classmethod from Pydantic v2."""

        return cls.parse_obj(data)

    def model_dump_json(self, **kwargs):
        """Provide ``model_dump_json`` compatible with v2."""

        return self.json(**kwargs)

    def model_copy(self, **kwargs):
        """Provide ``model_copy`` compatible with v2."""
     
        return self.copy(**kwargs)

    def model_construct(cls, _fields_set=None, **values):
        """Provide ``model_construct`` compatible with v2."""

        return cls.construct(_fields_set=_fields_set, **values)

    # Apply monkey patches so the rest of the code can rely on the v2 API
    pydantic.field_validator = field_validator
    BaseModel.model_validate = classmethod(model_validate)
    BaseModel.model_dump_json = model_dump_json
    BaseModel.model_copy = model_copy
    BaseModel.model_construct = classmethod(model_construct)
