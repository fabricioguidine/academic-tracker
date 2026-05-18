"""Load Scimago Journal Rank quartiles.

Download CSV from: https://www.scimagojr.com/journalrank.php (button 'Download data').
Scimago uses ';' as separator. Matches by exact lowercased title.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402


def main(path: Path) -> None:
    df = pd.read_csv(path, sep=";", dtype=str)
    cols = {c.lower().strip(): c for c in df.columns}
    title_col = cols.get("title")
    quartile_col = cols.get("sjr best quartile") or cols.get("quartile")
    if not (title_col and quartile_col):
        sys.exit(
            "Expected 'Title' and 'SJR Best Quartile' columns; "
            f"got {list(df.columns)}"
        )

    df = df[[title_col, quartile_col]].dropna()
    df.columns = ["title", "quartile"]
    df["title_norm"] = df["title"].str.lower().str.strip()

    conn = get_conn()
    try:
        venues = pd.read_sql_query(
            "SELECT venue_id, name FROM venues WHERE type = 'journal'",
            conn,
        )
        venues["name_norm"] = venues["name"].str.lower().str.strip()
        merged = venues.merge(df, left_on="name_norm",
                              right_on="title_norm", how="inner")
        for _, r in merged.iterrows():
            conn.execute(
                "UPDATE venues SET sjr_quartile = ? WHERE venue_id = ?",
                (r["quartile"], int(r["venue_id"])),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Updated SJR quartile for {len(merged)} journals.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    args = p.parse_args()
    main(args.csv)
