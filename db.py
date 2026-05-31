"""SQLite connection + schema bootstrap."""
from __future__ import annotations

import datetime as _dt
import os
import sqlite3
from pathlib import Path

# Python 3.12 deprecated the default date adapters; register explicit ISO ones.
sqlite3.register_adapter(_dt.date, lambda d: d.isoformat())
sqlite3.register_adapter(_dt.datetime, lambda d: d.isoformat())

ROOT = Path(__file__).parent
SCHEMA_PATH = ROOT / "schema.sql"


def db_path() -> Path:
    # ACADEMIC_TRACKER_DB lets tests (and alternate deployments) point at
    # another location; resolved per call so env changes take effect at runtime.
    override = os.environ.get("ACADEMIC_TRACKER_DB")
    return Path(override) if override else ROOT / "data" / "academic.db"


def get_conn() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
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
    print(f"Initialized {db_path()}")
