from pydantic import ValidationError
from .src_validator_models import PlanSchema

def validate_dsl(input_dict: dict) -> PlanSchema:
    """
    入力DSLを検証し、PlanSchemaオブジェクトを返す。
    エラーがあればValidationErrorを発生させる。
    """
    try:
        return PlanSchema.parse_obj(input_dict)
    except ValidationError as e:
        # ここでエラーメッセージを加工しても良い
        raise
