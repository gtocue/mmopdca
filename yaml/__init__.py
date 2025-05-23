import json

def safe_load(stream):
    if isinstance(stream, (str, bytes)):
        return json.loads(stream if isinstance(stream, str) else stream.decode())
    return {}

def safe_dump(data, *args, **kwargs):
    return json.dumps(data)