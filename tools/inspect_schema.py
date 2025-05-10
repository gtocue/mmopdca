# =========================================================
# ASSIST_KEY: 【tools/inspect_schema.py】 - SQLite スキーマ検査ツール
# =========================================================
#
# 【概要】
#   SQLite データベース（mmopdca.db）の `plan` および `do` テーブルの
#   カラム一覧を出力して、`created_at` が存在するかを確認します。
#
# 【使用方法】
#   PowerShell から以下のコマンドを実行:
#     python tools/inspect_schema.py
#
# 【備考】
#   - ファイル名を変更し、check_schema.py と混同しないようにしました。
#   - 任意の場所に配置可。実行時のカレントディレクトリに mmopdca.db を置いてください。
# ---------------------------------------------------------
import sqlite3
import sys

DB_FILE = "mmopdca.db"

def main():
    try:
        conn = sqlite3.connect(DB_FILE)
    except Exception as e:
        print(f"Error opening {DB_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    for tbl in ("plan", "do"):
        cursor = conn.execute(f"PRAGMA table_info('{tbl}');")
        cols = [row[1] for row in cursor.fetchall()]
        print(f"{tbl}: {cols}")

    conn.close()

if __name__ == "__main__":
    main()
