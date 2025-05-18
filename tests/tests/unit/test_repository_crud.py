# tests/unit/test_repository_crud.py

import uuid
import pytest
from core.repository.factory import get_repo

@pytest.fixture
def mem_repo():
    return get_repo("memory")

def test_crud_cycle(mem_repo):
    rec_id = f"rec-{uuid.uuid4().hex[:6]}"
    data = {"foo": "bar"}

    mem_repo.create(rec_id, data)
    assert mem_repo.get(rec_id) == data

    mem_repo.update(rec_id, {"foo": "baz"})
    assert mem_repo.get(rec_id)["foo"] == "baz"

    mem_repo.delete(rec_id)
    assert mem_repo.get(rec_id) is None
