import json
import urllib.request
import urllib.parse

class Response:
    def __init__(self, resp):
        self.status_code = resp.getcode()
        self.headers = dict(resp.headers)
        self._content = resp.read()
        self.text = self._content.decode()

    def json(self):
        return json.loads(self.text)

class RequestException(Exception):
    pass

def request(method, url, *, data=None, json=None, headers=None, timeout=None):
    if json is not None:
        data = json.dumps(json).encode()
        headers = headers or {}
        headers['Content-Type'] = 'application/json'
    if isinstance(data, str):
        data = data.encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Response(resp)
    except Exception as exc:  # pragma: no cover - basic error mapping
        raise RequestException(exc)

def get(url, **kwargs):
    return request('GET', url, **kwargs)

def post(url, **kwargs):
    return request('POST', url, **kwargs)