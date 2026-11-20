"""Week 2 - ask your own questions about the check-in data with SQL.

Run checkin_pipeline.py first. Then, from the repository root, either pass one query:
    python labs/week02/query.py "SELECT * FROM attendance LIMIT 5"
or start an interactive prompt (type a query and press Enter; an empty line quits):
    python labs/week02/query.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

DB_FILE = Path(__file__).resolve().parent / "data" / "week02.duckdb"


def signature() -> str:
    """Who ran the query and when: your screenshots show it."""
    try:
        when = f"{datetime.now(ZoneInfo('Asia/Bangkok')):%Y-%m-%d %H:%M} Bangkok time"
    except Exception:  # no time zone data on this computer
        when = f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC"
    user = os.environ.get("GITHUB_USER")  # set by GitHub in every codespace
    return f"run by @{user} on {when}" if user else f"run outside a codespace on {when}"


def run(con: duckdb.DuckDBPyConnection, sql: str) -> None:
    """Run one SQL statement and print its result as a table."""
    try:
        result = con.sql(sql)
    except duckdb.Error as err:
        print(f"SQL error: {err}")
        return
    if result is not None:
        result.show(max_rows=300)


def main() -> int:
    if not DB_FILE.exists():
        print("No database yet. Run this first:  python labs/week02/checkin_pipeline.py")
        return 1
    with duckdb.connect(str(DB_FILE), read_only=True) as con:
        if len(sys.argv) > 1:
            run(con, " ".join(sys.argv[1:]))
            print(f"-- query {signature()}")
            return 0
        tables = ", ".join(row[0] for row in con.execute("SHOW TABLES").fetchall())
        print(f"Tables: {tables}")
        print("Type a SQL query and press Enter. Press Enter on an empty line to quit.")
        while True:
            try:
                sql = input("sql> ").strip()
            except EOFError:
                break
            if not sql:
                break
            run(con, sql)
    return 0


if __name__ == "__main__":
    sys.exit(main())
