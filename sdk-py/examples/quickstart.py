# examples/quickstart.py

from mmopdca_sdk import Configuration, ApiClient
from mmopdca_sdk.api.plan_api import PlanApi
from mmopdca_sdk.models.plan_create_request import PlanCreateRequest

def main():
    # 1) 実際に動かしている API のベース URL を指定
    config = Configuration(
        host="http://localhost:8000"   # ← 適宜書き換えてください
    )

    # 2) ApiClient → PlanApi を初期化
    api_client = ApiClient(configuration=config)
    plan_api = PlanApi(api_client)

    # 3) リクエスト用モデルを作成
    req = PlanCreateRequest(
        symbol="AAPL",
        start="2025-05-01",
        end="2025-06-01"
    )

    # 4) 正しい呼び出し方
    #    ─ positionally ─
    resp1 = plan_api.create_plan_plan_post(req)

    #    ─ or keyword ─
    # resp2 = plan_api.create_plan_plan_post(plan_create_request=req)

    print("レスポンス:", resp1)

if __name__ == "__main__":
    main()
