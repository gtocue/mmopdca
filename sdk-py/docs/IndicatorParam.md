# IndicatorParam

追加計算したいテクニカル指標パラメータ。  *MVP* では `name=\"SMA\"` だけを想定するが、後方互換を考慮して 任意文字列を許容している。

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | 指標名 | [optional] [default to 'SMA']
**window** | **int** | 計算ウィンドウ（日／バー数） | [optional] [default to 5]

## Example

```python
from mmopdca_sdk.models.indicator_param import IndicatorParam

# TODO update the JSON string below
json = "{}"
# create an instance of IndicatorParam from a JSON string
indicator_param_instance = IndicatorParam.from_json(json)
# print the JSON string representation of the object
print(IndicatorParam.to_json())

# convert the object into a dict
indicator_param_dict = indicator_param_instance.to_dict()
# create an instance of IndicatorParam from a dict
indicator_param_from_dict = IndicatorParam.from_dict(indicator_param_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


