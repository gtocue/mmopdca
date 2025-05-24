from api.main_api import app
from starlette.testclient import TestClient

client = TestClient(app)

def test_get_trace_not_found():
    res = client.get("/trace/not_exist")
    assert res.status_code == 404
