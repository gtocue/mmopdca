# tests/test_factory.py
import pytest

from core.repository.factory import get_repo
from core.repository.redis_impl import RedisRepository
from core.repository.memory_impl import MemoryRepository
from core.repository.postgres_impl import PostgresRepository

@pytest.mark.parametrize(
    "backend,expect_cls",
    [
        ("memory", MemoryRepository),
        ("redis", RedisRepository),
        ("postgres", PostgresRepository),
    ],
)
def test_get_repo_switch(backend, expect_cls, monkeypatch):
    monkeypatch.setenv("DB_BACKEND", backend)
    # reload しなくて大丈夫 → get_repo 内で都度 os.getenv を参照
    repo = get_repo("dummy")
    assert isinstance(repo, expect_cls)

def test_crud_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_BACKEND", "memory")
    r = get_repo("toy")
    r.create("id1", {"foo": 1})
    assert r.get("id1") == {"foo": 1}
    r.delete("id1")
    assert r.get("id1") is None
