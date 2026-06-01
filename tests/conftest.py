"""Shared test fixtures.

Point the app at a throwaway SQLite file *before* anything imports ``db`` so
every test and every CLI subprocess (which inherits ``os.environ``) uses it.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_DB = Path(tempfile.gettempdir()) / "academic_tracker_test.db"
os.environ["ACADEMIC_TRACKER_DB"] = str(_DB)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Each test starts from an empty, freshly-initialised schema."""
    if _DB.exists():
        _DB.unlink()
    import db

    db.init_db()
    yield
    if _DB.exists():
        _DB.unlink()


@pytest.fixture
def repo_env():
    """Environment for CLI subprocesses, carrying the test DB path."""
    return {**os.environ, "ACADEMIC_TRACKER_DB": str(_DB)}
