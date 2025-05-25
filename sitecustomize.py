import importlib
import pydantic

if pydantic.__version__.startswith('1.'):
    from pydantic import BaseModel, validator

    def field_validator(*fields, mode='after'):
        pre = mode == 'before'
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

    pydantic.field_validator = field_validator
    BaseModel.model_validate = classmethod(model_validate)
    BaseModel.model_dump_json = model_dump_json
    BaseModel.model_copy = model_copy
    BaseModel.model_construct = classmethod(model_construct)import importlib
import pydantic

if pydantic.__version__.startswith('1.'):
    from pydantic import BaseModel, validator

    def field_validator(*fields, mode='after'):
        pre = mode == 'before'
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

    pydantic.field_validator = field_validator
    BaseModel.model_validate = classmethod(model_validate)
    BaseModel.model_dump_json = model_dump_json
    BaseModel.model_copy = model_copy
    BaseModel.model_construct = classmethod(model_construct)
