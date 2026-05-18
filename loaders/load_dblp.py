"""Fetch your DBLP publications by author PID.

Look up your PID at https://dblp.org (e.g. '123/4567'). Stores discovered venues
into the venues table (scope=INT) and prints the publication list.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

API = "https://dblp.org/pid/{pid}.xml"


def main(pid: str) -> None:
    r = requests.get(API.format(pid=pid), timeout=30,
                     headers={"User-Agent": "academic-tracker/0.1"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")

    pubs = []
    for entry in soup.find_all(["article", "inproceedings"]):
        title = entry.title.get_text(strip=True) if entry.title else ""
        if entry.journal:
            venue = entry.journal.get_text(strip=True)
            type_ = "journal"
        elif entry.booktitle:
            venue = entry.booktitle.get_text(strip=True)
            type_ = "conference"
        else:
            continue
        year = entry.year.get_text(strip=True) if entry.year else ""
        pubs.append((title, venue, year, type_))

    conn = get_conn()
    try:
        seen = set()
        for _title, venue, _year, type_ in pubs:
            if (venue, type_) in seen:
                continue
            seen.add((venue, type_))
            conn.execute(
                """INSERT INTO venues (name, type, scope)
                   VALUES (?, ?, 'INT')
                   ON CONFLICT(name, type) DO NOTHING""",
                (venue, type_),
            )
        conn.commit()
    finally:
        conn.close()

    print(f"Found {len(pubs)} DBLP entries; {len(seen)} unique venues stored.")
    for title, venue, year, _ in pubs:
        print(f"  {year}  [{venue}]  {title}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pid", help="DBLP PID like 123/4567")
    args = p.parse_args()
    main(args.pid)
