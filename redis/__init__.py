class Redis:
    """Simple in-memory Redis mock used for unit tests."""

    def __init__(self, *args, **kwargs):
        self._store = {}

    def set(self, key, value):
        self._store[key] = value

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        self._store.pop(key, None)

    def exists(self, *keys):
        """Return the count of existing keys."""
        return sum(1 for k in keys if k in self._store)

    def scan_iter(self, match="*"):
        if match.endswith("*"):
            prefix = match[:-1]
            return [k for k in list(self._store) if k.startswith(prefix)]
        return [k for k in list(self._store) if k == match]

    def ping(self):
        return True


def from_url(url, *args, **kwargs):
    """Return a new :class:`Redis` instance for the given URL."""

    return Redis()


__all__ = ["Redis", "from_url"]