try:  # Pydantic v2
    from pydantic import ConfigDict, field_validator  # type: ignore
    from pydantic import BaseModel  # type: ignore
except ImportError:  # pragma: no cover - pydantic v1 fallback
    from pydantic import BaseModel, validator  # type: ignore
    ConfigDict = dict  # type: ignore

    def field_validator(*fields, mode="after"):
        pre = mode == "before"
        def decorator(fn):
            return validator(*fields, pre=pre, allow_reuse=True)(fn)
        return decorator

    def model_validate(cls, data, **kwargs):
        return cls.parse_obj(data)

    def model_dump_json(self, **kwargs):
        return self.json(**kwargs)

    BaseModel.model_validate = classmethod(model_validate)
    BaseModel.model_dump_json = model_dump_json

__all__ = ["ConfigDict", "field_validator"]
