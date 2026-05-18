"""Helper for filling SBC event deadlines.

SBC's events portal does not expose a stable feed, so this script:
  1) Opens https://www.sbc.org.br/eventos in your browser
  2) Lists the SBC venues already in your DB so you know what to fill in
Then use the dashboard 'Add / Edit > New deadline' tab to enter dates.
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

SBC_ACRONYMS = [
    "SBBD", "SBES", "SBSeg", "SBRC", "WebMedia", "IHC", "BRACIS",
    "SIBGRAPI", "SBLP", "SBMF", "SBQS", "ENIAC", "WSCAD", "SBCARS",
    "SBSI", "ENANCIB",
]


def main(year: int) -> None:
    print(f"Year: {year}")
    print("SBC events portal: https://www.sbc.org.br/eventos")
    webbrowser.open("https://www.sbc.org.br/eventos")

    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT acronym, name FROM venues "
            f"WHERE acronym IN ({','.join('?' * len(SBC_ACRONYMS))}) "
            "ORDER BY acronym",
            SBC_ACRONYMS,
        ).fetchall()
    finally:
        conn.close()

    print(f"\nKnown SBC venues in DB ({len(rows)}):")
    for r in rows:
        print(f"  {r['acronym']}: {r['name']}")
    print("\nUse the dashboard 'Add / Edit > New deadline' tab to enter dates.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("year", type=int)
    args = p.parse_args()
    main(args.year)
