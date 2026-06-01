"""End-to-end tests: real schema, real CLI loaders, real Streamlit run.

These exercise the app the way a user does and are OS-agnostic (no shell
built-ins, paths via pathlib, subprocesses via ``sys.executable``), so the
same suite proves the app works on Linux, macOS and Windows in CI.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(args, env):
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_init_db_creates_all_tables():
    import db

    conn = db.get_conn()
    try:
        names = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()
    assert {"venues", "deadlines", "submissions"} <= names


def test_seed_cli_populates_venues(repo_env):
    res = _run(["seeds/seed.py"], repo_env)
    assert res.returncode == 0, res.stderr

    import db

    conn = db.get_conn()
    try:
        (count,) = conn.execute("SELECT COUNT(*) FROM venues").fetchone()
    finally:
        conn.close()
    assert count > 0


def test_load_core_cli_updates_rank(tmp_path, repo_env):
    import db

    conn = db.get_conn()
    try:
        conn.execute(
            "INSERT INTO venues (name, acronym, type, scope) "
            "VALUES ('My Conference', 'MYCONF', 'conference', 'INT')"
        )
        conn.commit()
    finally:
        conn.close()

    # CORE export: headerless, cols id,title,acronym,source,rank,...
    csv = tmp_path / "core.csv"
    csv.write_text("1,My Conference,MYCONF,Source,A,2024\n", encoding="utf-8")

    res = _run(["-m", "loaders.load_core", str(csv)], repo_env)
    assert res.returncode == 0, res.stderr

    conn = db.get_conn()
    try:
        (rank,) = conn.execute(
            "SELECT core FROM venues WHERE acronym = 'MYCONF'"
        ).fetchone()
    finally:
        conn.close()
    assert rank == "A"


def test_streamlit_app_runs_without_exception():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception


def test_streamlit_all_views_render():
    from streamlit.testing.v1 import AppTest

    for view in ["Deadlines", "Pipeline", "Venues", "Stats", "Add / Edit"]:
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        at.run()
        at.sidebar.radio[0].set_value(view).run()
        assert not at.exception, f"view {view!r} raised"


def test_db_path_honours_env_override(tmp_path, monkeypatch):
    import db

    target = tmp_path / "nested" / "custom.db"
    monkeypatch.setenv("ACADEMIC_TRACKER_DB", str(target))
    assert db.db_path() == target
    conn = db.get_conn()
    conn.close()
    assert target.exists()
