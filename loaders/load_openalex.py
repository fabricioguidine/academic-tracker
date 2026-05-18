"""Fetch your works from OpenAlex by ORCID.

Free, no key needed. ORCID format: 0000-0000-0000-0000.
Stores host venues into the venues table (scope=INT).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

API = "https://api.openalex.org/works"


def main(orcid: str) -> None:
    works: list[dict] = []
    cursor = "*"
    while cursor:
        r = requests.get(
            API, timeout=30,
            params={
                "filter": f"author.orcid:{orcid}",
                "per-page": 200,
                "cursor": cursor,
            },
            headers={"User-Agent": "academic-tracker/0.1"},
        )
        r.raise_for_status()
        data = r.json()
        works.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")

    conn = get_conn()
    try:
        seen = set()
        for w in works:
            host = (w.get("primary_location") or {}).get("source") or {}
            name = host.get("display_name")
            if not name:
                continue
            type_ = "journal" if host.get("type") == "journal" else "conference"
            if (name, type_) in seen:
                continue
            seen.add((name, type_))
            conn.execute(
                """INSERT INTO venues (name, type, scope)
                   VALUES (?, ?, 'INT')
                   ON CONFLICT(name, type) DO NOTHING""",
                (name, type_),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Fetched {len(works)} works from OpenAlex; "
          f"{len(seen)} unique venues stored.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("orcid", help="ORCID like 0000-0000-0000-0000")
    args = p.parse_args()
    main(args.orcid)
