"""mmopdca SDK package."""

__version__ = "1.0.0"

# The SDK modules pull in heavy dependencies (urllib3, pydantic v2, etc.).
# Import them lazily to keep the package importable in minimal environments.

def __getattr__(name: str):  # pragma: no cover - minimal fallback
    if name in {
        "ApiClient",
        "Configuration",
        "OpenApiException",
        "ApiTypeError",
        "ApiValueError",
        "ApiKeyError",
        "ApiAttributeError",
        "ApiException",
    }:
        from . import api_client as _api_client
        from . import configuration as _configuration
        from . import exceptions as _exc
        globals().update(
            {
                "ApiClient": _api_client.ApiClient,
                "Configuration": _configuration.Configuration,
                "OpenApiException": _exc.OpenApiException,
                "ApiTypeError": _exc.ApiTypeError,
                "ApiValueError": _exc.ApiValueError,
                "ApiKeyError": _exc.ApiKeyError,
                "ApiAttributeError": _exc.ApiAttributeError,
                "ApiException": _exc.ApiException,
            }
        )
        return globals()[name]
    raise AttributeError(name)

__all__ = [
    "ApiClient",
    "Configuration",
    "OpenApiException",
    "ApiTypeError",
    "ApiValueError",
    "ApiKeyError",
    "ApiAttributeError",
    "ApiException",
]