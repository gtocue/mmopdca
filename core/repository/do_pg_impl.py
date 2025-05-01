# =========================================================
# ASSIST_KEY: core/repository/do_pg_impl.py
# =========================================================
#
# DoRepository ― Do フェーズ結果を永続化する PostgreSQL リポジトリ
#   * 基底の PostgresRepository(JSONB 版) をほぼそのまま継承
#   * 将来、Do 専用インデックスや検索 API を足したい場合は
#     ここに override／utility を追加していく
# ---------------------------------------------------------

from __future__ import annotations

from core.repository.postgres_impl import PostgresRepository


class DoRepository(PostgresRepository):
    """
    Do テーブル専用 PostgreSQL Repository

    Parameters
    ----------
    schema : str, default "public"
        使用するスキーマ名。マルチテナント対応などで
        別スキーマを切りたい場合に上書き可能。
    """

    # テーブル名は固定で "do"
    def __init__(self, *, schema: str = "public") -> None:
        super().__init__(table="do", schema=schema)

    # -----------------------------------------------------------------
    # 将来拡張ポイント（例）
    # -----------------------------------------------------------------
    # def list_by_plan(self, plan_id: str) -> list[dict]:
    #     """
    #     指定 Plan に紐づく Do 結果を新しい順で返す。
    #     """
    #     q = """
    #         SELECT data
    #           FROM {schema}.do
    #          WHERE data->>'plan_id' = %s
    #          ORDER BY data->>'created_at' DESC
    #     """.format(schema=self.schema)
    #     return [row["data"] for row in self._execute(q, (plan_id,))]
