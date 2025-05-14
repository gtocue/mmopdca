# PlanResponse

Plan 取得／作成時に返す共通レスポンス。  旧クライアント互換の最小キー (id / symbol / start / end / created_at) 以外にも、DSL 全フィールドを残すため `extra=\"allow\"`。

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**symbol** | **str** |  | 
**start** | **date** |  | [optional] 
**end** | **date** |  | [optional] 
**created_at** | **str** |  | 

## Example

```python
from mmopdca_sdk.models.plan_response import PlanResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PlanResponse from a JSON string
plan_response_instance = PlanResponse.from_json(json)
# print the JSON string representation of the object
print(PlanResponse.to_json())

# convert the object into a dict
plan_response_dict = plan_response_instance.to_dict()
# create an instance of PlanResponse from a dict
plan_response_from_dict = PlanResponse.from_dict(plan_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


