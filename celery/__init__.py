from types import SimpleNamespace

class _States:
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

states = _States()


def shared_task(*dargs, **dkwargs):
    def decorator(fn):
        return fn
    return decorator

class Celery:
    def __init__(self, *args, broker=None, backend=None):
        self.conf = SimpleNamespace()
        self.conf.beat_schedule = {}
        self.conf.task_always_eager = False
        self.conf.update = lambda **kw: self.conf.__dict__.update(kw)
    def task(self, *dargs, **dkwargs):
        def decorator(fn):
            return fn
        return decorator
    def autodiscover_tasks(self, modules, related_name=None, force=False):
        pass
    def send_task(self, name, args=None, task_id=None, **kwargs):
        pass

__all__ = ["Celery", "states", "shared_task"]