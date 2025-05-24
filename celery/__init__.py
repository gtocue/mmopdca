from types import SimpleNamespace


class _Task:
    """Very small stand‑in for :class:`celery.Task`."""

    def __init__(self, fn, *, bind=False):
        self.fn = fn
        self.bind = bind
        self.__name__ = getattr(fn, "__name__", "task")

    def __call__(self, *args, **kwargs):
        if self.bind:
            ctx = SimpleNamespace(retry=lambda *a, **k: (_ for _ in ()).throw(Exception("retry")))
            return self.fn(ctx, *args, **kwargs)
        return self.fn(*args, **kwargs)

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self.__call__(*args, **kwargs)

    def apply_async(self, args=None, kwargs=None, **_):  # pragma: no cover
        return self.__call__(*(args or ()), **(kwargs or {}))

    delay = apply_async

class _States:
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

states = _States()


def shared_task(*dargs, **dkwargs):
    def decorator(fn):
        return _Task(fn, bind=dkwargs.get("bind", False))

    return decorator

class Celery:
    def __init__(self, *args, broker=None, backend=None):
        self.conf = SimpleNamespace()
        self.conf.beat_schedule = {}
        self.conf.task_always_eager = False
        self.conf.update = lambda **kw: self.conf.__dict__.update(kw)
        self._tasks = {}

    def task(self, *dargs, **dkwargs):
        def decorator(fn):
            name = dkwargs.get("name", fn.__name__)
            t = _Task(fn, bind=dkwargs.get("bind", False))
            self._tasks[name] = t
            return t

        return decorator

    def autodiscover_tasks(self, modules, related_name=None, force=False):
        for mod in modules:
            __import__(mod)

    def send_task(self, name, args=None, task_id=None, **kwargs):
        task = self._tasks.get(name)
        if not task:
            raise KeyError(f"Task {name!r} not found")
        return task(*(args or ()), **(kwargs or {}))


__all__ = ["Celery", "states", "shared_task", "_Task"]
