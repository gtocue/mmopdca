# MetricMeta


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**unit** | **str** |  | [optional] 
**slo** | **float** |  | [optional] 
**var_class** | **str** |  | 

## Example

```python
from mmopdca_sdk.models.metric_meta import MetricMeta

# TODO update the JSON string below
json = "{}"
# create an instance of MetricMeta from a JSON string
metric_meta_instance = MetricMeta.from_json(json)
# print the JSON string representation of the object
print(MetricMeta.to_json())

# convert the object into a dict
metric_meta_dict = metric_meta_instance.to_dict()
# create an instance of MetricMeta from a dict
metric_meta_from_dict = MetricMeta.from_dict(metric_meta_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


