"""Scrape WikiCFP for upcoming deadlines by topic.

Brittle: WikiCFP HTML changes occasionally. Use hand-curated topic queries.
Example: python -m loaders.load_wikicfp 'machine learning' databases security
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

SEARCH_URL = "http://www.wikicfp.com/cfp/servlet/tool.search"
HEADERS = {"User-Agent": "Mozilla/5.0 academic-tracker/0.1"}


def fetch_topic(topic: str) -> list[dict]:
    """Return list of {acronym_year, title, when, where, deadline, url} dicts."""
    r = requests.get(
        SEARCH_URL,
        params={"q": topic, "year": "f"},  # year=f → future events only
        timeout=30,
        headers=HEADERS,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    rows: list[dict] = []
    seen_urls = set()
    for a in soup.find_all("a", href=re.compile(r"event\.showcfp\?eventid=")):
        title_tr = a.find_parent("tr")
        if not title_tr:
            continue
        details_tr = title_tr.find_next_sibling("tr")
        if not details_tr:
            continue
        title_cells = title_tr.find_all("td")
        if len(title_cells) < 2:
            continue
        full_title = title_cells[1].get_text(strip=True)
        cells = details_tr.find_all("td")
        if len(cells) < 3:
            continue
        when = cells[0].get_text(strip=True)
        where = cells[1].get_text(strip=True)
        deadline = cells[2].get_text(strip=True)
        url = "http://www.wikicfp.com" + (a.get("href") or "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        rows.append({
            "acronym_year": a.get_text(strip=True),
            "title": full_title,
            "when": when,
            "where": where,
            "deadline": deadline,
            "url": url,
        })
    return rows


def parse_date(s: str):
    s = (s or "").strip()
    if not s or s.upper() == "TBD":
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_event_dates(when: str) -> tuple:
    """Parse 'Mon DD, YYYY - Mon DD, YYYY' → (start, end). Either may be None."""
    if not when:
        return (None, None)
    parts = [p.strip() for p in when.split("-")]
    start = parse_date(parts[0]) if parts else None
    end = parse_date(parts[1]) if len(parts) > 1 else None
    return (start, end)


def main(topics: list[str]) -> None:
    inserted = 0
    conn = get_conn()
    try:
        for topic in topics:
            events = fetch_topic(topic)
            print(f"[{topic}] {len(events)} events")
            for e in events:
                m = re.match(r"^(.+?)\s+(\d{4})$", e["acronym_year"])
                if m:
                    acronym, year = m.group(1).strip(), m.group(2)
                else:
                    acronym, year = e["acronym_year"], None
                name = e["title"] or e["acronym_year"]
                conn.execute(
                    """INSERT INTO venues (name, acronym, type, scope)
                       VALUES (?, ?, 'conference', 'INT')
                       ON CONFLICT(name, type) DO UPDATE SET
                         acronym = COALESCE(venues.acronym, excluded.acronym)""",
                    (name, acronym),
                )
                row = conn.execute(
                    "SELECT venue_id FROM venues "
                    "WHERE name = ? AND type = 'conference'",
                    (name,),
                ).fetchone()
                paper_due = parse_date(e["deadline"])
                event_start, event_end = parse_event_dates(e["when"])
                conn.execute(
                    """INSERT INTO deadlines
                       (venue_id, edition, paper_due,
                        event_start, event_end, location, cfp_url)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row["venue_id"], year, paper_due,
                     event_start, event_end,
                     e["where"] or None, e["url"]),
                )
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    print(f"Inserted {inserted} deadline rows.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "topics", nargs="+",
        help="WikiCFP search terms, e.g. 'machine learning' databases",
    )
    args = p.parse_args()
    main(args.topics)
