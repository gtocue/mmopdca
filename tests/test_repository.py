# tests/test_repository.py
import uuid
import pytest
from core.repository.factory import get_repo

@pytest.fixture(scope="function")
def mem_repo():
    """メモリ実装を返す。"""
    return get_repo("memory")

def test_crud_cycle(mem_repo):
    rec_id = f"rec-{uuid.uuid4().hex[:6]}"
    payload = {"foo": "bar"}

    # C
    mem_repo.create(rec_id, payload)
    # R
    assert mem_repo.get(rec_id) == payload
    # U
    mem_repo.update(rec_id, {"foo": "baz"})
    assert mem_repo.get(rec_id)["foo"] == "baz"
    # D
    mem_repo.delete(rec_id)
    assert mem_repo.get(rec_id) is None