# DoResponse

Do ジョブの状態および結果レスポンス。  `status` 遷移: **PENDING → RUNNING → (DONE | FAILED)**

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**do_id** | **str** | Do 実行 ID (&#x60;do-xxxx&#x60; 形式) | 
**plan_id** | **str** | 紐づく Plan ID | 
**seq** | **int** | DoCreateRequest.run_no のエコーバック（互換: &#39;seq&#39;） | 
**run_tag** | **str** |  | [optional] 
**status** | [**DoStatus**](DoStatus.md) | ジョブ状態 | 
**result** | **object** |  | [optional] 
**artifact_uri** | **str** |  | [optional] 
**dashboard_url** | **str** |  | [optional] 

## Example

```python
from mmopdca_sdk.models.do_response import DoResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DoResponse from a JSON string
do_response_instance = DoResponse.from_json(json)
# print the JSON string representation of the object
print(DoResponse.to_json())

# convert the object into a dict
do_response_dict = do_response_instance.to_dict()
# create an instance of DoResponse from a dict
do_response_from_dict = DoResponse.from_dict(do_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


