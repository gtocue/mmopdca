# =========================================================
# ASSIST_KEY: 【core/repository/redis_impl.py】
# =========================================================
#
# 【概要】
#   このユニットは RedisRepository として、
#   “シンプル Key-Value（1 Key ＝ 1 JSON）” な Repository を実装します。
#
# 【主な役割】
#   - create / get / update / delete / list の CRUD API を提供
#   - Redis をバックエンドに、Celery や API 間で共有出来る永続ストアを確保
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core.repository.factory.get_repo  … DI 入口
#       ・api/routers/do_api.py            … Do レコード CRUD
#   - 外部設定 :
#       ・環境変数 `REDIS_URL` で接続文字列を上書き可能
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない          # 該当なし
#   2) 市場名 suffix 規約は本ユニットでは非対象                    # 該当なし
#   3) **全体コード** を返却（本ファイルは完成形）
#   4) ヘッダー維持済み
#   5) 追加実装のみ。既存 API 互換
#   6) pdca_data 未使用。グローバル変数直書きも無し
#
# ---------------------------------------------------------

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Sequence

import redis  # redis-py

logger = logging.getLogger(__name__)


class RedisRepository:
    """
    1 Key = 1 JSON ドキュメントを保存する簡易ストア。

    * Redis key   : ``{prefix}:{id}``
    * Redis value : JSON 文字列
    """

    def __init__(
        self,
        table: str | None = None,
        *,
        key_prefix: str | None = None,  # ← v1 互換
        url: str | None = None,
        db: int = 1,  # FIXME: .env へ切り出し検討
        **redis_opts: Any,
    ) -> None:
        """
        Parameters
        ----------
        table / key_prefix
            - **新 API**: factory から `table="plan"` などが渡る
            - **旧 API**: 直接 `key_prefix="plan"`
            どちらかが使われる。両方 None なら 'mmop' を既定値にする。
        url / db / redis_opts
            redis.Redis へそのまま渡す接続情報
        """
        prefix = table or key_prefix or "mmop"
        self._prefix: str = f"{prefix}:"

        # --------------------------------------------------
        # 接続先 URL 生成
        #   • 明示引数 url が最優先
        #   • 次に環境変数 REDIS_URL
        #   • どちらも無ければ localhost をデフォルトにする
        #     （pytest をホスト OS 上で走らせても失敗しない）
        # --------------------------------------------------
        redis_url = (
            url
            or os.getenv("REDIS_URL")  # .env / シェルで与えられた値
            or f"redis://127.0.0.1:6379/{db}"  # フォールバック
        )

        # redis-py <4.0 does not provide ``redis.from_url``. Fall back to
        # ``Redis.from_url`` when necessary so unit tests run under the minimal
        # stubbed environment.
        from_url = getattr(redis, "from_url", None)
        if from_url is None:
            from_url = redis.Redis.from_url  # type: ignore[attr-defined]

        self._r: redis.Redis = from_url(
            redis_url,
            decode_responses=True,
            **redis_opts,
        )
        logger.debug("[RedisRepo] init prefix=%s url=%s", self._prefix, redis_url)

    # ------------------------------------------------------------------#
    # helpers
    # ------------------------------------------------------------------#
    def _k(self, id_: str) -> str:
        """内部: id -> Redis key"""
        return f"{self._prefix}{id_}"

    # ------------------------------------------------------------------#
    # public CRUD
    # ------------------------------------------------------------------#
    def create(self, id_: str, doc: Dict[str, Any]) -> None:
        """Upsert（存在すれば上書き）"""
        self._r.set(self._k(id_), json.dumps(doc))

    update = create  # エイリアス

    def get(self, id_: str) -> Dict[str, Any] | None:
        raw = self._r.get(self._k(id_))
        return json.loads(raw) if raw is not None else None

    def delete(self, id_: str) -> None:
        self._r.delete(self._k(id_))

    def list(self) -> List[Dict[str, Any]]:
        """prefix に一致するキーを全件取得（少量想定）"""
        docs: List[Dict[str, Any]] = []
        for key in self._scan_iter():
            raw = self._r.get(key)
            if raw is None:
                continue
            try:
                docs.append(json.loads(raw))
            except json.JSONDecodeError:  # pragma: no cover
                logger.warning("[RedisRepo] invalid JSON on key=%s", key)
        return docs

    # ------------------------------------------------------------------#
    # private
    # ------------------------------------------------------------------#
    def _scan_iter(self) -> Sequence[str]:
        """型アノテ付きラッパー"""
        return self._r.scan_iter(f"{self._prefix}*")


# --------------------------- self-test ---------------------------
if __name__ == "__main__":
    repo = RedisRepository(table="do_test")
    repo.create("abc", {"x": 1})
    data = repo.get("abc")
    assert data is not None and data["x"] == 1
    print("list:", repo.list())
    repo.delete("abc")
    print("✓ self-test OK")
