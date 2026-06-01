# Architecture

academic-tracker is a single-process, local-first Streamlit application backed
by an embedded SQLite database. There is no server, no account, and no network
dependency at runtime except the optional data loaders.

## Components

```
app.py            Streamlit UI — sidebar nav + five views (Deadlines, Pipeline,
                  Venues, Stats, Add / Edit). Reads/writes via db.get_conn().
db.py             SQLite connection + schema bootstrap. db_path() resolves the
                  database location (ACADEMIC_TRACKER_DB env var, else data/).
schema.sql        Declarative schema: venues, deadlines, submissions (+ indexes).
seeds/seed.py     Loads seeds/br_venues.csv into the venues table (idempotent).
loaders/          One module per external source. Each is runnable as a CLI
                  (python -m loaders.<name>) and writes into the active DB.
tests/            End-to-end pytest suite (see Testing).
```

## Data flow

1. `init_db()` runs `schema.sql` (idempotent `CREATE TABLE IF NOT EXISTS`).
2. `seeds/seed.py` and `loaders/*` populate/enrich `venues` and `deadlines`.
3. `app.py` queries the same SQLite file and renders interactive views.

All file paths are built with `pathlib.Path`, text I/O is explicitly UTF-8, and
SQLite date handling uses ISO adapters — so the code is byte-for-byte portable
across Linux, macOS and Windows.

## Cross-platform strategy

- No shell-outs or OS-specific paths in application code.
- DB location is overridable via `ACADEMIC_TRACKER_DB`, keeping tests hermetic.
- `.gitattributes` normalizes line endings to LF so checkouts are identical.
- CI (`.github/workflows/ci.yml`) runs the full suite on
  `ubuntu-latest`, `macos-latest`, and `windows-latest` across Python 3.11–3.13.

## Testing

`tests/test_e2e.py` exercises the app the way a user does:

- schema bootstrap creates all tables;
- `seeds/seed.py` and `loaders.load_core` run as real subprocesses against a
  throwaway DB and their effects are asserted in SQLite;
- the Streamlit app is launched headlessly via `streamlit.testing.v1.AppTest`
  and every view is rendered and checked for exceptions;
- the `ACADEMIC_TRACKER_DB` override is verified.

`tests/conftest.py` redirects the database to a temp file before `db` is
imported, so subprocesses inherit it through the environment.
