#!/usr/bin/env python3
# migrate_sqlite.py
# SQLite の plan/do テーブルに `created_at` カラムを追加するマイグレーションスクリプト

import sqlite3
import sys

DB_FILE = "mmopdca.db"


def ensure_column(conn, table: str, column: str, coltype: str = "TEXT"):
    """指定テーブルにカラムがなければ追加する。"""
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cursor.fetchall()]
    if column not in cols:
        print(f"Adding column `{column}` to `{table}`...")
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype};")
    else:
        print(f"`{table}` already has column `{column}`. Skipping.")


def main():
    try:
        conn = sqlite3.connect(DB_FILE)
    except Exception as e:
        print(f"Error opening {DB_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # plan テーブルに created_at
    ensure_column(conn, "plan", "created_at", "TEXT")
    # do テーブルに created_at
    ensure_column(conn, '"do"', "created_at", "TEXT")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
