# mmopdca_sdk.MetricsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_metric_value_metrics_name_get**](MetricsApi.md#get_metric_value_metrics_name_get) | **GET** /metrics/{name} | Get instant metric value
[**list_metrics_metrics_get**](MetricsApi.md#list_metrics_metrics_get) | **GET** /metrics/ | List metric catalog


# **get_metric_value_metrics_name_get**
> MetricValue get_metric_value_metrics_name_get(name)

Get instant metric value

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.metric_value import MetricValue
from mmopdca_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = mmopdca_sdk.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with mmopdca_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = mmopdca_sdk.MetricsApi(api_client)
    name = 'name_example' # str | 

    try:
        # Get instant metric value
        api_response = api_instance.get_metric_value_metrics_name_get(name)
        print("The response of MetricsApi->get_metric_value_metrics_name_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MetricsApi->get_metric_value_metrics_name_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  | 

### Return type

[**MetricValue**](MetricValue.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_metrics_metrics_get**
> List[MetricMeta] list_metrics_metrics_get()

List metric catalog

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.metric_meta import MetricMeta
from mmopdca_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = mmopdca_sdk.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with mmopdca_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = mmopdca_sdk.MetricsApi(api_client)

    try:
        # List metric catalog
        api_response = api_instance.list_metrics_metrics_get()
        print("The response of MetricsApi->list_metrics_metrics_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MetricsApi->list_metrics_metrics_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[MetricMeta]**](MetricMeta.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

