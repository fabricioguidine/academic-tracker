"""Load starter Brazilian venue list into DB."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

CSV_PATH = Path(__file__).parent / "br_venues.csv"


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    conn = get_conn()
    try:
        for r in rows:
            conn.execute(
                """INSERT INTO venues
                   (name, acronym, type, scope, area,
                    qualis, core, sjr_quartile, url, notes)
                   VALUES (:name, :acronym, :type, :scope, :area,
                           :qualis, :core, :sjr_quartile, :url, :notes)
                   ON CONFLICT(name, type) DO NOTHING""",
                {k: (v or None) for k, v in r.items()},
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Seeded {len(rows)} venues from {CSV_PATH.name}")


if __name__ == "__main__":
    main()
