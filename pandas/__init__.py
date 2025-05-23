class DataFrame(list):
    def __init__(self, data):
        keys = list(data.keys())
        rows = list(zip(*data.values()))
        super().__init__([{k: v[i] for k, v in data.items()} for i in range(len(rows))])
        self._columns = keys

    @property
    def columns(self):
        return self._columns

    def __len__(self):
        return super().__len__()