"""Re-check BR event sites that previously had no CFP content.

Run periodically (e.g. weekly via Task Scheduler). Prints a per-site report and
flags pages where CFP-relevant keywords newly appeared. State is persisted to
data/recheck_state.json so you can see *what changed* between runs.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "recheck_state.json"

SITES = [
    ("SBSeg",    "https://sbseg.sbc.org.br/2026/"),
    ("SBSeg",    "https://sbseg.sbc.org.br/"),
    ("SBMF",     "https://sbmf.sbc.org.br/2026/"),
    ("WSCAD",    "https://wscad.sbc.org.br/2026/"),
    ("WebMedia", "https://webmedia.sbc.org.br/2026/"),
    ("SIBGRAPI", "https://sibgrapi.sbc.org.br/2026/"),
    ("ENANCIB",  "http://enancib.ancib.org/"),
]

# Keywords that suggest a CFP page has been populated.
CFP_KEYWORDS = [
    "deadline", "submission", "submissão", "submissao", "prazo",
    "data limite", "important dates", "datas importantes",
    "abstract", "camera-ready", "notification", "notificação",
    "call for papers", "chamada de trabalhos", "trilha principal",
]

HEADERS = {"User-Agent": "Mozilla/5.0 academic-tracker/0.1"}
EMPTY_TEXT_BYTES = 200  # below this, page is essentially blank


def _strip(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "header", "nav", "footer"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def check_one(url: str) -> dict:
    try:
        r = requests.get(url, timeout=20, headers=HEADERS,
                         verify=False, allow_redirects=True)
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:120]}"}

    text = _strip(r.text)
    text_lower = text.lower()
    keywords_found = sorted({k for k in CFP_KEYWORDS if k in text_lower})
    return {
        "ok": True,
        "status": r.status_code,
        "final_url": r.url,
        "raw_bytes": len(r.content),
        "text_bytes": len(text),
        "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        "keywords": keywords_found,
        "is_blank": len(text) < EMPTY_TEXT_BYTES,
    }


def main() -> None:
    state = _load_state()
    today = dt.date.today().isoformat()
    changes: list[str] = []

    print(f"Re-check run @ {today}")
    print("=" * 78)

    for name, url in SITES:
        prev = state.get(url, {})
        cur = check_one(url)
        cur["checked_at"] = today

        if not cur.get("ok"):
            print(f"  {name:9s} {url}\n             ERROR: {cur['error']}")
        else:
            tag = (
                "blank"
                if cur["is_blank"]
                else f"{cur['text_bytes']}b, {len(cur['keywords'])} kw"
            )
            print(f"  {name:9s} [{cur['status']}] {tag:24s} {url}")
            if cur["keywords"]:
                print(f"             keywords: {', '.join(cur['keywords'])}")

            new_keywords = sorted(set(cur["keywords"]) - set(prev.get("keywords", [])))
            content_changed = (
                prev.get("text_hash")
                and prev.get("text_hash") != cur.get("text_hash")
            )
            if new_keywords:
                changes.append(
                    f"  [NEW] {name}: new CFP keywords found "
                    f"({', '.join(new_keywords)}) -- review {url}"
                )
            elif content_changed and not cur["is_blank"]:
                changes.append(f"  [CHG] {name}: content changed -- review {url}")

        state[url] = cur

    _save_state(state)

    print("=" * 78)
    if changes:
        print("Changes since last run:")
        for c in changes:
            print(c)
    else:
        print("No new CFP content detected since last run.")
    print(f"\nState saved to {STATE_PATH}")


if __name__ == "__main__":
    main()
