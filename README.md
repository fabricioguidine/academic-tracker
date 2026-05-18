# academic-tracker

Local Streamlit dashboard to track academic publication venues (CS / Information Sciences) — deadlines, submission pipeline, and rankings. Brazil-first (Qualis CAPES, SBC events) with international support (CORE, Scimago/SJR, DBLP, OpenAlex, WikiCFP).

## Setup

```bash
cd C:\Users\fabri\academic-tracker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python db.py                    # initialize SQLite schema
python seeds/seed.py            # load starter Brazilian venue list
streamlit run app.py            # opens http://localhost:8501
```

## Loaders

All loaders write into `data/academic.db`. Run only what you need.

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

## Roadmap

- Lattes XML import (`scriptLattes`) for existing CV
- Auto-refresh DBLP nightly via Windows Task Scheduler
- Topic preferences saved per-user, used to filter WikiCFP
- BR ↔ INT acronym map for cross-ranking joins
