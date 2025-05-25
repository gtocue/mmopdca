import importlib
import pydantic

"""Backport a subset of Pydantic v2 APIs when running under v1 and
apply small compatibility patches for test utilities."""

# ---------------------------------------------------------------------------
# Pydantic v1 compatibility shims
# ---------------------------------------------------------------------------
if pydantic.__version__.startswith("1."):
    from pydantic import BaseModel, validator

    def field_validator(*fields, mode="after"):
        """Shim for ``pydantic.v2.field_validator``."""
        pre = mode == "before"

        def decorator(fn):
            return validator(*fields, pre=pre, allow_reuse=True)(fn)
        
        return decorator

    def model_validate(cls, data):
        return cls.parse_obj(data)

    def model_dump_json(self, **kwargs):
        return self.json(**kwargs)

    def model_copy(self, **kwargs):
        return self.copy(**kwargs)

    def model_construct(cls, _fields_set=None, **values):
        return cls.construct(_fields_set=_fields_set, **values)

    from pydantic import root_validator

    def model_validator(mode="after"):
        def decorator(fn):
            return root_validator(pre=mode == "before", allow_reuse=True)(fn)
        return decorator

    # Expose the shims
    pydantic.field_validator = field_validator
    pydantic.model_validator = model_validator
    setattr(BaseModel, "model_validate", classmethod(model_validate))
    BaseModel.model_dump_json = model_dump_json
    BaseModel.model_copy = model_copy
    setattr(BaseModel, "model_construct", classmethod(model_construct))

# ---------------------------------------------------------------------------
# FastAPI / Starlette compatibility patches
# ---------------------------------------------------------------------------
try:
    from fastapi.testclient import TestClient as _TestClient
    import inspect

    if "stream" not in inspect.signature(_TestClient.get).parameters:
        _orig_get = _TestClient.get

        def _patched_get(self, url, *, stream=False, **kwargs):
            response = _orig_get(self, url, **kwargs)
            return response

        _TestClient.get = _patched_get
except Exception:  # pragma: no cover - optional
    pass