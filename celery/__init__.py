from types import SimpleNamespace


class _Task:
    """Very small stand‑in for :class:`celery.Task`."""

    def __init__(self, fn):
        self.fn = fn
        self.__name__ = getattr(fn, "__name__", "task")

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self.fn(*args, **kwargs)

    def apply_async(self, args=None, kwargs=None, **_):  # pragma: no cover
        return self.fn(*(args or ()), **(kwargs or {}))

    delay = apply_async

class _States:
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

states = _States()


def shared_task(*dargs, **dkwargs):
    def decorator(fn):
        return _Task(fn)

    return decorator

class Celery:
    def __init__(self, *args, broker=None, backend=None):
        self.conf = SimpleNamespace()
        self.conf.beat_schedule = {}
        self.conf.task_always_eager = False
        self.conf.update = lambda **kw: self.conf.__dict__.update(kw)
    def task(self, *dargs, **dkwargs):
        def decorator(fn):
            return _Task(fn)

        return decorator
    def autodiscover_tasks(self, modules, related_name=None, force=False):
        pass
    def send_task(self, name, args=None, task_id=None, **kwargs):
        pass

__all__ = ["Celery", "states", "shared_task", "_Task"]