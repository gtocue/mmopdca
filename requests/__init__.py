import json as _json
import urllib.request
from types import SimpleNamespace

class Response:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self.content = content
    def json(self):
        return _json.loads(self.content.decode())
    def text(self):
        return self.content.decode()

class RequestException(Exception):
    pass

def _request(method, url, *, data=None, json=None, timeout=None, headers=None):
    if json is not None:
        data = _json.dumps(json).encode()
        headers_dict = {'Content-Type': 'application/json'}
    else:
        headers_dict = {}
    hdrs = {**(headers or {}), **headers_dict}
    if isinstance(data, str):
        data = data.encode()
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Response(resp.getcode(), dict(resp.headers), resp.read())
    except Exception as exc:
        raise RequestException(str(exc)) from exc

def get(url, **kwargs):
    return _request('GET', url, **kwargs)

def post(url, **kwargs):
    return _request('POST', url, **kwargs)