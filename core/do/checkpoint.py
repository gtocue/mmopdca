# =========================================================
# ASSIST_KEY: 【core/do/checkpoint.py】
# =========================================================
#
# 【概要】
#   このユニットは Checkpoint ユーティリティとして、
#   “長時間ジョブの途中経過を安全に永続化／復元” する機能を実装します。
#
# 【主な役割】
#   - 任意の Python dict を JSON ファイルで保存（save_ckpt）
#   - 最新のチェックポイント読み込み（load_latest_ckpt）
#   - 完了フラグ用の “done-sentinel” を生成 / 検出
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core/do/coredo_executor.py  … epoch ごとに呼び出し
#       ・core/celery_app.py          … duplicate guard で利用
#   - 外部設定 :
#       ・環境変数 CKPT_DIR, CKPT_EVERY_N_MIN
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は "Close_Nikkei_225" / "Open_SP500" のように suffix で区別
#   3) **全体コード** を返却（スニペットではなくファイルの完成形）
#   4) ファイル冒頭に必ず本ヘッダーを残すこと
#   5) 機能削除や breaking change は事前相談（原則 “追加” のみ）
#   6) pdca_data[...] キーに統一し、グローバル変数直書き禁止
#
# 【注意事項】
#   - ハードコード値を見つけたら「TODO: 外部設定へ」のコメントを添付
#   - インターフェース変更時は docs/ARCH.md を必ず更新
#   - 型安全重視 (Pydantic / typing)・ハルシネーション厳禁
# ---------------------------------------------------------

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# ────────────────────────────────
# ロガー
# ────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ────────────────────────────────
# 定数 / 環境変数
# ────────────────────────────────

def _resolve_ckpt_dir() -> Path:
    """
    チェックポイント保存先を決定する。

    優先順位:
    1. 環境変数 CKPT_DIR
    2. コンテナマウント想定の /mnt/checkpoints
    3. ~/.cache/mmopdca/checkpoints
    4. ./checkpoints  (プロジェクト直下 — 最終フォールバック)

    どのディレクトリも作成可能になるまで優先順に試す。
    """
    # 1) 明示指定
    env_dir = os.getenv("CKPT_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    # 2) コンテナマウント想定のパス
    mnt_dir = Path("/mnt/checkpoints")
    try:
        mnt_dir.mkdir(parents=True, exist_ok=True)
        return mnt_dir
    except PermissionError:
        logger.warning("cannot write to %s; falling back", mnt_dir)

    # 3) ホーム配下 (GitHub Actions でも書き込み可能)
    home_dir = Path.home() / ".cache" / "mmopdca" / "checkpoints"
    try:
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir
    except PermissionError:
        logger.warning("cannot write to %s; falling back to ./checkpoints", home_dir)

    # 4) カレント直下
    return (Path.cwd() / "checkpoints").resolve()

# 確定パス
CKPT_DIR: Path = _resolve_ckpt_dir()
CKPT_DIR.mkdir(parents=True, exist_ok=True)

# チェックポイント間隔（分）
CKPT_INT_MIN = int(os.getenv("CKPT_EVERY_N_MIN", "15"))  # TODO: 外部設定へ

# ────────────────────────────────
# 内部ユーティリティ
# ────────────────────────────────

def _ckpt_path(plan_id: str, epoch_idx: int, *, ts: int | None = None) -> Path:
    """checkpoint ファイル名を一意に生成."""
    ts_part = ts if ts is not None else int(time.time())
    return CKPT_DIR / f"{plan_id}__{epoch_idx:04d}_{ts_part}.json"


def _done_path(plan_id: str, epoch_idx: int) -> Path:
    """完了済み sentinel."""
    return CKPT_DIR / f"{plan_id}__{epoch_idx:04d}_done"

# ────────────────────────────────
# Public API
# ────────────────────────────────

def save_ckpt(plan_id: str, epoch_idx: int, state: Dict[str, Any]) -> Path:
    """
    現在の state を JSON で保存し、パスを返す。

    * state はシリアライズ可能な dict を期待。
    * I/O エラーは例外のまま呼び元へ伝播。
    """
    fp = _ckpt_path(plan_id, epoch_idx)
    fp.write_text(json.dumps(state, ensure_ascii=False))
    logger.debug("checkpoint saved %s (%d bytes)", fp.name, fp.stat().st_size)
    return fp


def load_latest_ckpt(plan_id: str, epoch_idx: int) -> Optional[Dict[str, Any]]:
    """
    指定 shard の最新 checkpoint を読み込む。

    1 件も無い場合は None を返す。
    """
    pattern = f"{plan_id}__{epoch_idx:04d}_*.json"
    ckpts = sorted(
        CKPT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not ckpts:
        logger.debug("no checkpoint found for %s epoch %d", plan_id, epoch_idx)
        return None

    fp = ckpts[0]
    try:
        data = json.loads(fp.read_text())
        logger.info(
            "checkpoint loaded %s (%s)",
            fp.name,
            datetime.fromtimestamp(fp.stat().st_mtime),
        )
        return data
    except json.JSONDecodeError as exc:
        logger.error("corrupted checkpoint %s: %s", fp, exc)
        return None


def mark_done(plan_id: str, epoch_idx: int) -> None:
    """
    epoch 完了を sentinel でマーク（空ファイル）。

    Celery duplicate-guard が存在チェックで利用。
    """
    _done_path(plan_id, epoch_idx).touch()
    logger.debug("done sentinel created for %s epoch %d", plan_id, epoch_idx)


def is_done(plan_id: str, epoch_idx: int) -> bool:
    """完了 sentinel が存在するか判定."""
    return _done_path(plan_id, epoch_idx).exists()

# ────────────────────────────────
# CLI デバッグ用
# ────────────────────────────────
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="checkpoint debug helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    _save = sub.add_parser("save")
    _save.add_argument("plan_id")
    _save.add_argument("epoch", type=int)
    _save.add_argument("json_str", help="state as JSON string")

    _load = sub.add_parser("load")
    _load.add_argument("plan_id")
    _load.add_argument("epoch", type=int)

    _done = sub.add_parser("done")
    _done.add_argument("plan_id")
    _done.add_argument("epoch", type=int)

    args = parser.parse_args()

    if args.cmd == "save":
        save_ckpt(args.plan_id, args.epoch, json.loads(args.json_str))
    elif args.cmd == "load":
        print(json.dumps(load_latest_ckpt(args.plan_id, args.epoch), indent=2))
    elif args.cmd == "done":
        mark_done(args.plan_id, args.epoch)
    else:
        sys.exit("unknown command")
