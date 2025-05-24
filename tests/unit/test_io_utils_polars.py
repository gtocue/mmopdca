from pathlib import Path
import types

import core.common.io_utils as io


def test_save_predictions_with_polars(monkeypatch, tmp_path):
    class DummyPLDataFrame(list):
        def __init__(self, data):
            super().__init__(list(data))

        def write_parquet(self, path, compression=None, statistics=True):
            Path(path).write_text("dummy")

    class DummyPLModule(types.SimpleNamespace):
        DataFrame = DummyPLDataFrame

        def __call__(self, data):
            return DummyPLDataFrame(data)

    dummy_pl = DummyPLModule()
    monkeypatch.setattr(io, "pl", dummy_pl, raising=False)
    monkeypatch.setattr(io, "_DF_LIB", "polars")
    monkeypatch.setattr(io, "_HAS_PARQUET", True)

    df = [{"a": 1}]
    path = io.save_predictions(df, "plan_x", "run_y")

    assert Path(path).exists()