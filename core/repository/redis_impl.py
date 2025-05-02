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

import redis

# NOTE: redis-py は decode_responses=True で str ⇔ str に統一
logger = logging.getLogger(__name__)


class RedisRepository:
    """
    シンプルな Key-Value JSON ストア。

    * key = ``{prefix}:{id}``
    * value = JSON 文字列
    """

    def __init__(
        self,
        key_prefix: str,
        *,
        url: str | None = None,
        db: int = 1,  # FIXME: ハードコード - .env に切り出す
    ) -> None:
        redis_url = url or os.getenv("REDIS_URL", f"redis://redis:6379/{db}")
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix: str = f"{key_prefix}:"
        logger.debug("[RedisRepo] init prefix=%s url=%s", self._prefix, redis_url)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _k(self, id_: str) -> str:  # noqa: D401
        """内部: id → Redis key"""
        return f"{self._prefix}{id_}"

    # ------------------------------------------------------------------ #
    # public CRUD
    # ------------------------------------------------------------------ #
    def create(self, id_: str, doc: Dict[str, Any]) -> None:
        """Upsert と同義。"""
        self._r.set(self._k(id_), json.dumps(doc))

    # upsert 用エイリアス
    update = create

    def get(self, id_: str) -> Dict[str, Any] | None:
        v = self._r.get(self._k(id_))
        return json.loads(v) if v is not None else None

    def delete(self, id_: str) -> None:
        self._r.delete(self._k(id_))

    def list(self) -> List[Dict[str, Any]]:
        """prefix に一致するキーを全件スキャンして返す（少量データ想定）。"""
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

    # ------------------------------------------------------------------ #
    # private
    # ------------------------------------------------------------------ #
    def _scan_iter(self) -> Sequence[str]:
        """ラッパー – 型アノテーションを付けただけ。"""
        # TODO: 大量件数なら SSCAN + cursor 管理で chunk 取得に置き換える
        return self._r.scan_iter(f"{self._prefix}*")


# ================================ test stub ===============================
if __name__ == "__main__":  # 簡易動作確認
    repo = RedisRepository("do_test")
    repo.create("abc", {"x": 1})
    assert repo.get("abc")["x"] == 1
    assert len(repo.list()) >= 1
    repo.delete("abc")
    print("self-test ok")
