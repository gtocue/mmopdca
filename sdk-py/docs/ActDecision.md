# ActDecision


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | act-xxxx 一意 ID | 
**check_id** | **str** | 紐づく Check ID | 
**decided_at** | **datetime** | UTC ISO8601 | 
**action** | [**ActAction**](ActAction.md) |  | 
**reason** | **str** | 意思決定根拠 (人間可読) | 

## Example

```python
from mmopdca_sdk.models.act_decision import ActDecision

# TODO update the JSON string below
json = "{}"
# create an instance of ActDecision from a JSON string
act_decision_instance = ActDecision.from_json(json)
# print the JSON string representation of the object
print(ActDecision.to_json())

# convert the object into a dict
act_decision_dict = act_decision_instance.to_dict()
# create an instance of ActDecision from a dict
act_decision_from_dict = ActDecision.from_dict(act_decision_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


