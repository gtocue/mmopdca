# CheckResult

/check エンドポイントのレスポンス & ストレージフォーマット report はタスク未完了時に None を返すケースを考慮

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | check-xxxx 形式の一意 ID | 
**do_id** | **str** | 評価対象の Do ID | 
**created_at** | **datetime** | UTC ISO8601 | 
**report** | [**Report**](Report.md) |  | [optional] 

## Example

```python
from mmopdca_sdk.models.check_result import CheckResult

# TODO update the JSON string below
json = "{}"
# create an instance of CheckResult from a JSON string
check_result_instance = CheckResult.from_json(json)
# print the JSON string representation of the object
print(CheckResult.to_json())

# convert the object into a dict
check_result_dict = check_result_instance.to_dict()
# create an instance of CheckResult from a dict
check_result_from_dict = CheckResult.from_dict(check_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


