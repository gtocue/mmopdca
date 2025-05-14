# mmopdca_sdk.CheckApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**enqueue_check_check_do_id_post**](CheckApi.md#enqueue_check_check_do_id_post) | **POST** /check/{do_id} | Enqueue Check job (Celery)
[**get_check_check_check_id_get**](CheckApi.md#get_check_check_check_id_get) | **GET** /check/{check_id} | Get Check record
[**get_check_status_check_status_task_id_get**](CheckApi.md#get_check_status_check_status_task_id_get) | **GET** /check/status/{task_id} | Raw Celery task state
[**list_check_check_get**](CheckApi.md#list_check_check_get) | **GET** /check/ | List Check records


# **enqueue_check_check_do_id_post**
> object enqueue_check_check_do_id_post(do_id)

Enqueue Check job (Celery)

Check フェーズのタスクを Celery に登録 & 初期レコードを作成

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
    api_instance = mmopdca_sdk.CheckApi(api_client)
    do_id = 'do_id_example' # str | 

    try:
        # Enqueue Check job (Celery)
        api_response = api_instance.enqueue_check_check_do_id_post(do_id)
        print("The response of CheckApi->enqueue_check_check_do_id_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CheckApi->enqueue_check_check_do_id_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **do_id** | **str**|  | 

### Return type

**object**

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_check_check_check_id_get**
> CheckResult get_check_check_check_id_get(check_id)

Get Check record

永続化されたチェックレコードを返却

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.check_result import CheckResult
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
    api_instance = mmopdca_sdk.CheckApi(api_client)
    check_id = 'check_id_example' # str | 

    try:
        # Get Check record
        api_response = api_instance.get_check_check_check_id_get(check_id)
        print("The response of CheckApi->get_check_check_check_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CheckApi->get_check_check_check_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **check_id** | **str**|  | 

### Return type

[**CheckResult**](CheckResult.md)

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

# **get_check_status_check_status_task_id_get**
> object get_check_status_check_status_task_id_get(task_id)

Raw Celery task state

Celery タスクの生ステータスおよびエラーを取得

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
    api_instance = mmopdca_sdk.CheckApi(api_client)
    task_id = 'task_id_example' # str | 

    try:
        # Raw Celery task state
        api_response = api_instance.get_check_status_check_status_task_id_get(task_id)
        print("The response of CheckApi->get_check_status_check_status_task_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CheckApi->get_check_status_check_status_task_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_id** | **str**|  | 

### Return type

**object**

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

# **list_check_check_get**
> List[CheckResult] list_check_check_get()

List Check records

保存済みの Check レコードをすべて返却

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.check_result import CheckResult
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
    api_instance = mmopdca_sdk.CheckApi(api_client)

    try:
        # List Check records
        api_response = api_instance.list_check_check_get()
        print("The response of CheckApi->list_check_check_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CheckApi->list_check_check_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[CheckResult]**](CheckResult.md)

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

