# academic-tracker

Local Streamlit dashboard to track academic publication venues (CS / Information Sciences) — deadlines, submission pipeline, and rankings. Brazil-first (Qualis CAPES, SBC events) with international support (CORE, Scimago/SJR, DBLP, OpenAlex, WikiCFP).

Runs on Linux, macOS and Windows. Every push is tested on all three via the CI matrix.

## Setup

Requires Python 3.11+.

**Linux / macOS**

```bash
git clone https://github.com/fabricioguidine/academic-tracker.git
cd academic-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python db.py              # initialize SQLite schema
python seeds/seed.py      # load starter Brazilian venue list
streamlit run app.py      # opens http://localhost:8501
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/fabricioguidine/academic-tracker.git
cd academic-tracker
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python db.py
python seeds\seed.py
streamlit run app.py
```

The database lives at `data/academic.db` by default. Set the `ACADEMIC_TRACKER_DB`
environment variable to point at another location (used by the test suite).

## Loaders

All loaders write into the active database. Run only what you need.

| Loader | Source | How |
|---|---|---|
| `load_qualis` | CAPES Qualis (BR journals/conferences) | Download XLSX from [Sucupira](https://sucupira.capes.gov.br/sucupira/public/consultas/coleta/veiculoPublicacaoQualis/listaConsultaGeralPeriodicos.jsf), then `python -m loaders.load_qualis path/to/qualis.xlsx` |
| `load_core` | CORE (INT, CS conferences) | Export CSV from [portal.core.edu.au](http://portal.core.edu.au/conf-ranks/), then `python -m loaders.load_core core.csv` |
| `load_sjr` | Scimago JR (INT journals) | Download CSV from [scimagojr.com](https://www.scimagojr.com/journalrank.php), then `python -m loaders.load_sjr scimago.csv` |
| `load_dblp` | DBLP (your CS publications) | Look up your PID at dblp.org, then `python -m loaders.load_dblp 123/4567` |
| `load_openalex` | OpenAlex (your publications + venues) | `python -m loaders.load_openalex 0000-0000-0000-0000` |
| `load_wikicfp` | WikiCFP deadlines (INT) | `python -m loaders.load_wikicfp "machine learning" databases` |
| `load_sbc` | SBC events portal (BR) | `python -m loaders.load_sbc 2026` (opens browser; deadlines added manually via dashboard) |

## Schema

- **venues** — `name, acronym, type (conference/journal/workshop), scope (BR/INT/both), area, qualis, core, sjr_quartile, h5, url, notes`
- **deadlines** — `abstract_due, paper_due, notification, camera_ready, event_start, location, cfp_url`
- **submissions** — `title, venue_id, status (idea → drafting → submitted → under_review → revision → accepted/rejected → published), topics, coauthors, notes`

## Views

- **Deadlines** — upcoming CFPs in a window, filterable by scope/Qualis/CORE
- **Pipeline** — kanban-style by submission status
- **Venues** — full venue list, filterable
- **Stats** — submissions by status, acceptance rate
- **Add / Edit** — manual entry for submissions, venues, deadlines

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite is end-to-end: it boots the schema, runs the CLI loaders as real
subprocesses, and drives the Streamlit app via `streamlit.testing` — so a green
run proves the app actually works on the host OS. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Roadmap

- Lattes XML import (`scriptLattes`) for existing CV
- Auto-refresh DBLP nightly (cron / Task Scheduler)
- Topic preferences saved per-user, used to filter WikiCFP
- BR ↔ INT acronym map for cross-ranking joins
