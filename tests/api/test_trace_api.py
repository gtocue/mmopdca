# tests/api/test_trace_api.py

import pytest
from fastapi import status
from datetime import datetime, timezone
from api.routers.trace_api import router as trace_router
from fastapi.testclient import TestClient
from core.repository.factory import get_repo

@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(trace_router)
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_trace_repo(tmp_path, monkeypatch):
    """
    Trace リポジトリをメモリ実装に差し替え。
    テスト用に run_id 'test-run' が存在するようセットアップ。
    """
    repo = get_repo("trace")
    # テスト間で状態が残らないようストアをクリア
    if hasattr(repo, "keys"):
        for k in getattr(repo, "keys")():
            repo.delete(k)

    # run_id 'test-run' として空レコードを準備
    if hasattr(repo, "upsert"):
        getattr(repo, "upsert")("test-run", {})
    else:
        try:
            repo.create("test-run", {})
        except KeyError:
            pass
    return repo

def test_trace_stream_success(client):
    """
    正常系: 存在する run_id でストリーミング開始レスポンスを受け取れること
    """
    if hasattr(client, "stream"):
        with client.stream("GET", "/trace/test-run") as response:
            assert response.status_code == status.HTTP_200_OK
            lines = []
            for chunk in response.iter_lines():
                if chunk:
                    lines.append(chunk.decode())
                if len(lines) >= 2:
                    break
    else:
        response = client.get("/trace/test-run")
        assert response.status_code == status.HTTP_200_OK
        lines = response.text.splitlines()

    assert lines[0].startswith("data: ")
    assert "run_id" in lines[0]

def test_trace_stream_not_found(client):
    """
    異常系: 存在しない run_id では 404 エラーになること
    """
    response = client.get("/trace/unknown-run")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "run_id not found"