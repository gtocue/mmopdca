# mmopdca_sdk.PlanDslApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_plan_dsl_plan_dsl_post**](PlanDslApi.md#create_plan_dsl_plan_dsl_post) | **POST** /plan-dsl/ | Create Plan from DSL (YAML / JSON)
[**get_plan_dsl_plan_dsl_plan_id_get**](PlanDslApi.md#get_plan_dsl_plan_dsl_plan_id_get) | **GET** /plan-dsl/{plan_id} | Get DSL Plan
[**list_plans_dsl_plan_dsl_get**](PlanDslApi.md#list_plans_dsl_plan_dsl_get) | **GET** /plan-dsl/ | List DSL Plans


# **create_plan_dsl_plan_dsl_post**
> PlanResponse create_plan_dsl_plan_dsl_post(file=file)

Create Plan from DSL (YAML / JSON)

DSL ファイル *または* 生テキスト body を受け取り Plan を登録。

**PowerShell 例**

```powershell
$yaml = Get-Content .\samples\plan_mvp.yaml -Raw
Invoke-RestMethod `
  -Uri 'http://localhost:8001/plan-dsl/' `
  -Method Post `
  -Body $yaml `
  -ContentType 'application/x-yaml'
```

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
    api_instance = mmopdca_sdk.PlanDslApi(api_client)
    file = None # bytearray |  (optional)

    try:
        # Create Plan from DSL (YAML / JSON)
        api_response = api_instance.create_plan_dsl_plan_dsl_post(file=file)
        print("The response of PlanDslApi->create_plan_dsl_plan_dsl_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanDslApi->create_plan_dsl_plan_dsl_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file** | **bytearray**|  | [optional] 

### Return type

[**PlanResponse**](PlanResponse.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_plan_dsl_plan_dsl_plan_id_get**
> PlanResponse get_plan_dsl_plan_dsl_plan_id_get(plan_id)

Get DSL Plan

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
    api_instance = mmopdca_sdk.PlanDslApi(api_client)
    plan_id = 'plan_id_example' # str | 

    try:
        # Get DSL Plan
        api_response = api_instance.get_plan_dsl_plan_dsl_plan_id_get(plan_id)
        print("The response of PlanDslApi->get_plan_dsl_plan_dsl_plan_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanDslApi->get_plan_dsl_plan_dsl_plan_id_get: %s\n" % e)
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

# **list_plans_dsl_plan_dsl_get**
> List[PlanResponse] list_plans_dsl_plan_dsl_get()

List DSL Plans

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
    api_instance = mmopdca_sdk.PlanDslApi(api_client)

    try:
        # List DSL Plans
        api_response = api_instance.list_plans_dsl_plan_dsl_get()
        print("The response of PlanDslApi->list_plans_dsl_plan_dsl_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PlanDslApi->list_plans_dsl_plan_dsl_get: %s\n" % e)
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

