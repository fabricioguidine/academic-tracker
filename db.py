"""SQLite connection + schema bootstrap."""
from __future__ import annotations

import datetime as _dt
import sqlite3
from pathlib import Path

# Python 3.12 deprecated the default date adapters; register explicit ISO ones.
sqlite3.register_adapter(_dt.date, lambda d: d.isoformat())
sqlite3.register_adapter(_dt.datetime, lambda d: d.isoformat())

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "academic.db"
SCHEMA_PATH = ROOT / "schema.sql"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
