# mmopdca_sdk.ActApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_act_act_check_id_post**](ActApi.md#create_act_act_check_id_post) | **POST** /act/{check_id} | Run Act (decide next action)
[**get_act_act_act_id_get**](ActApi.md#get_act_act_act_id_get) | **GET** /act/{act_id} | Get ActDecision
[**list_act_act_get**](ActApi.md#list_act_act_get) | **GET** /act/ | List ActDecision


# **create_act_act_check_id_post**
> ActDecision create_act_act_check_id_post(check_id)

Run Act (decide next action)

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.act_decision import ActDecision
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
    api_instance = mmopdca_sdk.ActApi(api_client)
    check_id = 'check_id_example' # str | Check ID to act on

    try:
        # Run Act (decide next action)
        api_response = api_instance.create_act_act_check_id_post(check_id)
        print("The response of ActApi->create_act_act_check_id_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActApi->create_act_act_check_id_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **check_id** | **str**| Check ID to act on | 

### Return type

[**ActDecision**](ActDecision.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_act_act_act_id_get**
> ActDecision get_act_act_act_id_get(act_id)

Get ActDecision

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.act_decision import ActDecision
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
    api_instance = mmopdca_sdk.ActApi(api_client)
    act_id = 'act_id_example' # str | 

    try:
        # Get ActDecision
        api_response = api_instance.get_act_act_act_id_get(act_id)
        print("The response of ActApi->get_act_act_act_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActApi->get_act_act_act_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **act_id** | **str**|  | 

### Return type

[**ActDecision**](ActDecision.md)

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

# **list_act_act_get**
> List[ActDecision] list_act_act_get()

List ActDecision

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.act_decision import ActDecision
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
    api_instance = mmopdca_sdk.ActApi(api_client)

    try:
        # List ActDecision
        api_response = api_instance.list_act_act_get()
        print("The response of ActApi->list_act_act_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActApi->list_act_act_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ActDecision]**](ActDecision.md)

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

