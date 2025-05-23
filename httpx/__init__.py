import json
import urllib.parse
import urllib.request
from types import SimpleNamespace

class Request:
    def __init__(self, method: str, url: str, headers=None, stream=None):
        self.method = method
        self.url = urllib.parse.urlparse(url)
        self.headers = headers or {}
        self.stream = stream or ByteStream(b"")

class Response:
    def __init__(self, status_code: int = 200, headers=None, content: bytes = b"", request: Request | None = None):
        self.status_code = status_code
        self.headers = headers or {}
        self._content = content
        self.request = request

    def read(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self._content.decode()

    def json(self):
        return json.loads(self._content.decode())

class ByteStream(bytes):
    def read(self) -> bytes:  # pragma: no cover - compatibility
        return bytes(self)

class BaseTransport:
    def handle_request(self, request: Request) -> Response:  # pragma: no cover
        raise NotImplementedError

class Client:
    def __init__(self, *, app=None, base_url: str = "", headers=None, transport: BaseTransport | None = None, follow_redirects: bool = True, cookies=None):
        self.app = app
        self.base_url = urllib.parse.urlparse(base_url)
        self.headers = headers or {}
        self.transport = transport
        self.follow_redirects = follow_redirects
        self.cookies = cookies

    def request(self, method: str, url: str, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=None, follow_redirects=None, timeout=None, extensions=None):
        target = urllib.parse.urljoin(self.base_url.geturl(), url)
        req = Request(method, target, headers={**self.headers, **(headers or {})}, stream=ByteStream(content or b""))
        if self.transport is not None:
            return self.transport.handle_request(req)
        data = content
        if json is not None:
            data = json.dumps(json).encode()
            headers = headers or {}
            headers['Content-Type'] = 'application/json'
            req.headers.update(headers)
        with urllib.request.urlopen(target, data=data, timeout=timeout) as resp:
            return Response(resp.getcode(), dict(resp.headers), resp.read(), req)

    def get(self, url: str, **kwargs) -> Response:
        return self.request('GET', url, **kwargs)

    def post(self, url: str, content=None, data=None, json=None, **kwargs) -> Response:
        return self.request('POST', url, content=content, data=data, json=json, **kwargs)

    def close(self):
        pass

class _UseClientDefault:
    pass

USE_CLIENT_DEFAULT = _UseClientDefault()
CookieTypes = object
TimeoutTypes = object

class _Types(SimpleNamespace):
    URLTypes = object
    QueryParamTypes = object
    HeaderTypes = object
    RequestContent = object
    RequestFiles = object
    AuthTypes = object
    CookieTypes = object

_types = _Types()

class _ClientModule(SimpleNamespace):
    USE_CLIENT_DEFAULT = USE_CLIENT_DEFAULT
    UseClientDefault = _UseClientDefault
    CookieTypes = object
    TimeoutTypes = object

_client = _ClientModule()

import sys
sys.modules[__name__ + '._types'] = _types
sys.modules[__name__ + '._client'] = _client

__all__ = [
    'Request',
    'Response',
    'ByteStream',
    'BaseTransport',
    'Client',
    'USE_CLIENT_DEFAULT',
]