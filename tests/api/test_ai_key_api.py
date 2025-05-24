import httpx

from api.main_api import app

client = httpx.Client(app=app, base_url="http://test")

def test_ai_key_flow():
    # 1) 新規発行
    res = client.post("/ai-key/")
    assert res.status_code == 201
    body = res.json()
    key_id = body["id"]
    assert len(body["key"]) > 40

    # 2) 取得
    res2 = client.get(f"/ai-key/{key_id}")
    assert res2.status_code == 200
    assert res2.json()["key"] == body["key"]
