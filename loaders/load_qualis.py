"""Load CAPES Qualis classification from a downloaded XLSX.

Get the file from Sucupira:
  https://sucupira.capes.gov.br/sucupira/public/consultas/coleta/veiculoPublicacaoQualis/listaConsultaGeralPeriodicos.jsf

Required columns (any spelling): Title (Título / Periódico) and Tier (Estrato / Qualis).
Matches by exact lowercased title against venues already in the DB.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn  # noqa: E402

TITLE_COLS = ["Título", "Title", "TITULO", "Periódico", "PERIODICO"]
TIER_COLS = ["Estrato", "Qualis", "ESTRATO", "Classificação"]


def _pick(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None


def main(path: Path) -> None:
    df = pd.read_excel(path)
    title_col = _pick(df.columns, TITLE_COLS)
    tier_col = _pick(df.columns, TIER_COLS)
    if not (title_col and tier_col):
        sys.exit(f"Could not find title/tier columns. Got: {list(df.columns)}")

    df = df[[title_col, tier_col]].dropna()
    df.columns = ["title", "tier"]
    df["title_norm"] = df["title"].astype(str).str.lower().str.strip()

    conn = get_conn()
    try:
        venues = pd.read_sql_query("SELECT venue_id, name FROM venues", conn)
        venues["name_norm"] = venues["name"].str.lower().str.strip()
        merged = venues.merge(df, left_on="name_norm",
                              right_on="title_norm", how="inner")
        for _, r in merged.iterrows():
            conn.execute(
                "UPDATE venues SET qualis = ? WHERE venue_id = ?",
                (r["tier"], int(r["venue_id"])),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Updated qualis for {len(merged)}/{len(venues)} venues "
          f"(matched by exact title).")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("xlsx", type=Path)
    args = p.parse_args()
    main(args.xlsx)
