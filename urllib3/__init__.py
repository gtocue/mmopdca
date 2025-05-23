class HTTPResponse:
    pass
class PoolManager:
    def __init__(self, *args, **kwargs):
        pass
    def request(self, *args, **kwargs):
        raise NotImplementedError('HTTP requests not supported in stub')
class Timeout:
    def __init__(self, *args, **kwargs):
        pass
class exceptions:
    class SSLError(Exception):
        pass