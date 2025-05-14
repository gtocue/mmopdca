import os
from datetime import date

from mmopdca_sdk.api.plan_api import PlanApi
from mmopdca_sdk.models import PlanCreateRequest, Expression
from mmopdca_sdk.configuration import Configuration


def main():
    # API キーを環境変数から取得
    api_key = os.getenv("API_KEY", "your-api-key-here")

    # クライアント設定
    config = Configuration()
    config.api_key["x-api-key"] = api_key
    client = PlanApi(configuration=config)

    # PlanCreateRequest に必須フィールドをすべて渡す
    request = PlanCreateRequest(
        symbol="AAPL",                      # 銘柄シンボル
        name="my-first-plan",               # プラン名
        start=date(2021, 1, 1),              # 開始日 (YYYY, M, D)
        end=date(2021, 12, 31),              # 終了日
        expressions=[                        # 式リスト
            Expression(
                name="moving_average",    # 指標名
                expression="average(window=3)"
            )
        ]
    )

    # プランを作成
    response = client.create_plan(request)
    print("Created plan:", response)


if __name__ == "__main__":
    main()
