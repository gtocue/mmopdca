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
    # run_id 'test-run' として、空の状態を用意
    repo.create("test-run", {})
    return repo

def test_trace_stream_success(client):
    """
    正常系: 存在する run_id でストリーミング開始レスポンスを受け取れること
    """
    response = client.get("/trace/test-run", stream=True)
    assert response.status_code == status.HTTP_200_OK
    # 最初の数行を読み込んで SSE フォーマットを確認
    lines = []
    for chunk in response.iter_lines():
        if chunk:
            lines.append(chunk.decode())
        if len(lines) >= 2:
            break
    assert lines[0].startswith("data: ")
    assert "run_id" in lines[0]

def test_trace_stream_not_found(client):
    """
    異常系: 存在しない run_id では 404 エラーになること
    """
    response = client.get("/trace/unknown-run")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "run_id not found"
