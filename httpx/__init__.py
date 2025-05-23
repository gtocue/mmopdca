import json as _json
import urllib.parse
import urllib.request
from types import SimpleNamespace
import uuid


class URL:
    """Minimal URL implementation used by the test stubs."""

    def __init__(self, url: str = "") -> None:
        self._url = urllib.parse.urlsplit(url)

    def join(self, other: str) -> "URL":
        return URL(urllib.parse.urljoin(self._url.geturl(), other))

    # Properties accessed by Starlette's TestClient
    @property
    def scheme(self) -> str:
        return self._url.scheme

    @property
    def netloc(self) -> bytes:
        return self._url.netloc.encode()

    @property
    def path(self) -> str:
        return self._url.path

    @property
    def raw_path(self) -> bytes:
        return self._url.path.encode()

    @property
    def query(self) -> bytes:
        return self._url.query.encode()

    def geturl(self) -> str:  # pragma: no cover - compatibility
        return self._url.geturl()

    def __str__(self) -> str:  # pragma: no cover - debug
        return self._url.geturl()

class Headers(dict):
    """Minimal headers container supporting the API used in tests."""

    def multi_items(self):
        return list(self.items())


class Request:
    def __init__(self, method: str, url: str, headers=None, stream=None):
        self.method = method
        self.url = URL(url)
        self.headers = Headers(headers or {})
        self.stream = stream or ByteStream(b"")

    def read(self) -> bytes:
        return self.stream.read()

class Response:
    def __init__(self, status_code: int = 200, headers=None, content: bytes = b"", stream=None, request: Request | None = None):
        self.status_code = status_code
        self.headers = Headers(headers or {})
        if stream is not None:
            content = stream.read()
        self._content = content
        self.request = request

    def read(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self._content.decode()

    def json(self):
        return _json.loads(self._content.decode())

class ByteStream(bytes):
    def read(self) -> bytes:  # pragma: no cover - compatibility
        return bytes(self)

class BaseTransport:
    def handle_request(self, request: Request) -> Response:  # pragma: no cover
        raise NotImplementedError

class Client:
    def __init__(self, *, app=None, base_url: str = "", headers=None, transport: BaseTransport | None = None, follow_redirects: bool = True, cookies=None):
        self.app = app
        self.base_url = URL(base_url)
        self.headers = Headers(headers or {})
        self.transport = transport
        self.follow_redirects = follow_redirects
        self.cookies = cookies

    def _merge_url(self, url: str | URL) -> URL:
        if isinstance(url, URL):
            return self.base_url.join(url.geturl())
        return self.base_url.join(str(url))

    def request(self, method: str, url: str, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=None, follow_redirects=None, timeout=None, extensions=None):
        target = self._merge_url(url).geturl()
        if files is not None:
            boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
            body = bytearray()
            for name, (filename, filecontent, ctype) in files.items():
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(f"Content-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\n".encode())
                body.extend(f"Content-Type: {ctype}\r\n\r\n".encode())
                body.extend(filecontent if isinstance(filecontent, bytes) else str(filecontent).encode())
                body.extend(b"\r\n")
            body.extend(f"--{boundary}--\r\n".encode())
            content = bytes(body)
            headers = headers or {}
            headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        merged_headers = {}
        merged_headers.update(self.headers)
        merged_headers.update(headers or {})
        req = Request(method, target, headers=merged_headers, stream=ByteStream(content or b""))
        if self.transport is not None:
            return self.transport.handle_request(req)
        data = content
        if json is not None:
            data = _json.dumps(json).encode()
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
    'Headers',
    'BaseTransport',
    'Client',
    'USE_CLIENT_DEFAULT',
]