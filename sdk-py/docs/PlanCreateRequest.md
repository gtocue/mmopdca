# PlanCreateRequest

Plan 作成リクエスト。  * `id` を省略した場合はルーター側で UUID を自動採番。 * `symbol / start / end` は旧 API 互換の最小セット。

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**symbol** | **str** | メイン銘柄ティッカー | 
**start** | **date** | 学習開始日 (ISO-8601) | 
**end** | **date** | 学習終了日 (ISO-8601) | 

## Example

```python
from mmopdca_sdk.models.plan_create_request import PlanCreateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PlanCreateRequest from a JSON string
plan_create_request_instance = PlanCreateRequest.from_json(json)
# print the JSON string representation of the object
print(PlanCreateRequest.to_json())

# convert the object into a dict
plan_create_request_dict = plan_create_request_instance.to_dict()
# create an instance of PlanCreateRequest from a dict
plan_create_request_from_dict = PlanCreateRequest.from_dict(plan_create_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


