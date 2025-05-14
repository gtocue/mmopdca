# mmopdca_sdk.PlanApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_plan_plan_post**](PlanApi.md#create_plan_plan_post) | **POST** /plan/ | Create Plan
[**delete_plan_plan_plan_id_delete**](PlanApi.md#delete_plan_plan_plan_id_delete) | **DELETE** /plan/{plan_id} | Delete Plan
[**get_plan_plan_plan_id_get**](PlanApi.md#get_plan_plan_plan_id_get) | **GET** /plan/{plan_id} | Get Plan by ID
[**list_plans_plan_get**](PlanApi.md#list_plans_plan_get) | **GET** /plan/ | List Plans


# **create_plan_plan_post**
> PlanResponse create_plan_plan_post(plan_create_request)

Create Plan

新しい Plan を登録する。

* `id` を省略すると `plan_<8桁>` を自動採番。
* 同じ `id` が既にあれば **409 Conflict**。

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.plan_create_request import PlanCreateRequest
from mmopdca_sdk.models.plan_response import PlanResponse
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
    api_instance = mmopdca_sdk.PlanApi(api_client)
    plan_create_request = mmopdca_sdk.PlanCreateRequest() # PlanCreateRequest | 

    try:
        # Create Plan
        api_response = api_instance.create_plan_plan_post(plan_create_request)
        print("The response of PlanApi->create_plan_plan_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanApi->create_plan_plan_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **plan_create_request** | [**PlanCreateRequest**](PlanCreateRequest.md)|  | 

### Return type

[**PlanResponse**](PlanResponse.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_plan_plan_plan_id_delete**
> delete_plan_plan_plan_id_delete(plan_id)

Delete Plan

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
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
    api_instance = mmopdca_sdk.PlanApi(api_client)
    plan_id = 'plan_id_example' # str | 

    try:
        # Delete Plan
        api_instance.delete_plan_plan_plan_id_delete(plan_id)
    except Exception as e:
        print("Exception when calling PlanApi->delete_plan_plan_plan_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **plan_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_plan_plan_plan_id_get**
> PlanResponse get_plan_plan_plan_id_get(plan_id)

Get Plan by ID

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.plan_response import PlanResponse
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
    api_instance = mmopdca_sdk.PlanApi(api_client)
    plan_id = 'plan_id_example' # str | 

    try:
        # Get Plan by ID
        api_response = api_instance.get_plan_plan_plan_id_get(plan_id)
        print("The response of PlanApi->get_plan_plan_plan_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanApi->get_plan_plan_plan_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **plan_id** | **str**|  | 

### Return type

[**PlanResponse**](PlanResponse.md)

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

# **list_plans_plan_get**
> List[PlanResponse] list_plans_plan_get()

List Plans

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.plan_response import PlanResponse
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
    api_instance = mmopdca_sdk.PlanApi(api_client)

    try:
        # List Plans
        api_response = api_instance.list_plans_plan_get()
        print("The response of PlanApi->list_plans_plan_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanApi->list_plans_plan_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[PlanResponse]**](PlanResponse.md)

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

