# CheckReport

可変キーを許容する緩いメトリクスモデル。 デフォルト項目として r2 / threshold / passed を持ち、 追加指標 (rmse, mape など) は extra=\"allow\" で拡張可能。

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**r2** | **float** | 決定係数 | 
**threshold** | **float** | 合格ライン | 
**passed** | **bool** | 閾値をクリアしたら True | 

## Example

```python
from mmopdca_sdk.models.check_report import CheckReport

# TODO update the JSON string below
json = "{}"
# create an instance of CheckReport from a JSON string
check_report_instance = CheckReport.from_json(json)
# print the JSON string representation of the object
print(CheckReport.to_json())

# convert the object into a dict
check_report_dict = check_report_instance.to_dict()
# create an instance of CheckReport from a dict
check_report_from_dict = CheckReport.from_dict(check_report_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


