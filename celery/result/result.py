from .. import states

class AsyncResult:
    def __init__(self, task_id):
        self.id = task_id
        self.task_id = task_id
        self.state = states.SUCCESS
        self.result = None