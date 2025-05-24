import json
from urllib import request as _request

class Response:
    def __init__(self, status_code: int, headers: dict, content: bytes):
        self.status_code = status_code
        self.headers = headers
        self._content = content

    def json(self):
        return json.loads(self._content.decode())

    def text(self):
        return self._content.decode()


def _make_request(method: str, url: str, *, data=None, json_data=None):
    if json_data is not None:
        data = json.dumps(json_data).encode()
        headers = {"Content-Type": "application/json"}
    else:
        headers = {}
    if isinstance(data, str):
        data = data.encode()
    req = _request.Request(url, data=data, headers=headers, method=method.upper())
    with _request.urlopen(req) as resp:
        return Response(resp.getcode(), dict(resp.headers), resp.read())


def get(url: str, **kwargs):
    return _make_request("GET", url, **kwargs)


def post(url: str, json=None, data=None, **kwargs):
    return _make_request("POST", url, data=data, json_data=json)