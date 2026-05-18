"""Load CORE conference rankings.

Export CSV from: http://portal.core.edu.au/conf-ranks/?search=&by=all&do=Export
The export has no header. Columns: id, title, acronym, source, rank, ...
Matches by acronym (uppercased) against conference venues in the DB.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402


def main(path: Path) -> None:
    df = pd.read_csv(path, header=None, usecols=[1, 2, 4],
                     names=["title", "acronym", "rank"], dtype=str)
    df = df.dropna(subset=["acronym", "rank"])
    df["acronym_norm"] = df["acronym"].str.upper().str.strip()

    conn = get_conn()
    try:
        venues = pd.read_sql_query(
            "SELECT venue_id, acronym FROM venues "
            "WHERE type = 'conference' AND acronym IS NOT NULL",
            conn,
        )
        venues["acronym_norm"] = venues["acronym"].str.upper().str.strip()
        merged = venues.merge(df, on="acronym_norm", how="inner")
        for _, r in merged.iterrows():
            conn.execute(
                "UPDATE venues SET core = ? WHERE venue_id = ?",
                (r["rank"], int(r["venue_id"])),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Updated CORE rank for {len(merged)} conferences.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    args = p.parse_args()
    main(args.csv)
