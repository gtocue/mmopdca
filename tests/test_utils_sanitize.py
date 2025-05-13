# =========================================================
# ASSIST_KEY: このファイルは【tests/test_utils_sanitize.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは test_utils_sanitize として、
#   utils.sanitize_for_serialization のユニットテストを提供します。
#
# 【主な役割】
#   - 様々な型（プリミティブ／datetime／Decimal／dict／list／Pydanticモデル／独自オブジェクト）に対し
#     sanitize_for_serialization が期待どおりの変換を行うことを検証
#
# 【連携先・依存関係】
#   - テスト対象: utils/__init__.py の sanitize_for_serialization
#   - 依存: pytest, pydantic
#
# 【ルール遵守】
#   1) ハードコード値はテスト内限定
#   2) 型安全: typing を活用
#   3) テストは pytest で実行可能
#
# 【注意事項】
#   - ハルシネーション厳禁
#   - fixtures は使用せず、各テストで直接検証
#
# ---------------------------------------------------------

import datetime
import decimal

from pydantic import BaseModel

from utils import sanitize_for_serialization


def test_primitive_types():
    assert sanitize_for_serialization(42) == 42
    assert sanitize_for_serialization(3.14) == 3.14
    assert sanitize_for_serialization(True) is True
    assert sanitize_for_serialization("hello") == "hello"
    assert sanitize_for_serialization(None) is None


def test_datetime_and_date():
    dt = datetime.datetime(2025, 5, 13, 12, 0, 0)
    assert sanitize_for_serialization(dt) == "2025-05-13T12:00:00"
    d = datetime.date(2025, 5, 13)
    assert sanitize_for_serialization(d) == "2025-05-13"


def test_decimal_type():
    dec = decimal.Decimal("12.34")
    assert sanitize_for_serialization(dec) == "12.34"


def test_dict_and_iterables():
    obj = {
        "a": [1, decimal.Decimal("2.2"), datetime.date(2025, 5, 13)],
        "b": ("x", False)
    }
    result = sanitize_for_serialization(obj)
    assert isinstance(result, dict)
    assert result["a"][0] == 1
    assert result["a"][1] == "2.2"
    assert result["a"][2] == "2025-05-13"
    assert result["b"] == ["x", False]


def test_pydantic_model():
    class DummyModel(BaseModel):
        x: int
        y: str

    model = DummyModel(x=5, y="test")
    result = sanitize_for_serialization(model)
    assert isinstance(result, dict)
    assert result == {"x": 5, "y": "test"}


def test_fallback_for_custom_object():
    class Custom:
        def __str__(self):
            return "custom"

    obj = Custom()
    assert sanitize_for_serialization(obj) == "custom"
