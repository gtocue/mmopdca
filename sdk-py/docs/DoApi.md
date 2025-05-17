# mmopdca_sdk.DoApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**enqueue_do_do_plan_id_post**](DoApi.md#enqueue_do_do_plan_id_post) | **POST** /do/{plan_id} | Enqueue Do job (Celery)
[**get_do_do_do_id_get**](DoApi.md#get_do_do_do_id_get) | **GET** /do/{do_id} | Get Do record
[**get_do_status_do_status_task_id_get**](DoApi.md#get_do_status_do_status_task_id_get) | **GET** /do/status/{task_id} | Raw Celery task state
[**list_do_do_get**](DoApi.md#list_do_do_get) | **GET** /do/ | List Do records


# **enqueue_do_do_plan_id_post**
> Dict[str, str] enqueue_do_do_plan_id_post(plan_id, do_create_request=do_create_request)

Enqueue Do job (Celery)

Plan に紐づく Do フェーズのジョブを Celery に enqueue（または同期実行）する。

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.do_create_request import DoCreateRequest
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
    api_instance = mmopdca_sdk.DoApi(api_client)
    plan_id = 'plan_id_example' # str | 
    do_create_request = mmopdca_sdk.DoCreateRequest() # DoCreateRequest |  (optional)

    try:
        # Enqueue Do job (Celery)
        api_response = api_instance.enqueue_do_do_plan_id_post(plan_id, do_create_request=do_create_request)
        print("The response of DoApi->enqueue_do_do_plan_id_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoApi->enqueue_do_do_plan_id_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **plan_id** | **str**|  | 
 **do_create_request** | [**DoCreateRequest**](DoCreateRequest.md)|  | [optional] 

### Return type

**Dict[str, str]**

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_do_do_do_id_get**
> DoResponse get_do_do_do_id_get(do_id)

Get Do record

do_id で指定した Do レコードを返す。

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.do_response import DoResponse
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
    api_instance = mmopdca_sdk.DoApi(api_client)
    do_id = 'do_id_example' # str | 

    try:
        # Get Do record
        api_response = api_instance.get_do_do_do_id_get(do_id)
        print("The response of DoApi->get_do_do_do_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoApi->get_do_do_do_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **do_id** | **str**|  | 

### Return type

[**DoResponse**](DoResponse.md)

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

# **get_do_status_do_status_task_id_get**
> object get_do_status_do_status_task_id_get(task_id)

Raw Celery task state

Celery の AsyncResult を使って、タスクの生の状態を返す。

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
    api_instance = mmopdca_sdk.DoApi(api_client)
    task_id = 'task_id_example' # str | 

    try:
        # Raw Celery task state
        api_response = api_instance.get_do_status_do_status_task_id_get(task_id)
        print("The response of DoApi->get_do_status_do_status_task_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoApi->get_do_status_do_status_task_id_get: %s\n" % e)
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

# **list_do_do_get**
> List[DoResponse] list_do_do_get()

List Do records

保存済みの全 Do レコード一覧を返す。

### Example

* Api Key Authentication (APIKeyHeader):

```python
import mmopdca_sdk
from mmopdca_sdk.models.do_response import DoResponse
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
    api_instance = mmopdca_sdk.DoApi(api_client)

    try:
        # List Do records
        api_response = api_instance.list_do_do_get()
        print("The response of DoApi->list_do_do_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoApi->list_do_do_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[DoResponse]**](DoResponse.md)

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

