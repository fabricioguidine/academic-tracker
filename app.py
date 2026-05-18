"""Academic-tracker dashboard."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from db import get_conn, init_db

st.set_page_config(page_title="Academic Tracker", page_icon=":books:", layout="wide")
init_db()

PIPELINE_STATUSES = [
    "idea", "drafting", "submitted", "under_review",
    "revision", "accepted", "rejected", "published", "withdrawn",
]


@st.cache_data(ttl=30)
def load_table(name: str) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(f"SELECT * FROM {name}", conn)
    finally:
        conn.close()


def refresh():
    st.cache_data.clear()


# ---------- Sidebar ----------
st.sidebar.title("Academic Tracker")
view = st.sidebar.radio(
    "View",
    ["Deadlines", "Pipeline", "Venues", "Stats", "Add / Edit"],
)
scope_filter = st.sidebar.multiselect(
    "Scope", ["BR", "INT", "both"], default=["BR", "INT", "both"]
)
st.sidebar.divider()
st.sidebar.caption("Loaders run from CLI:")
st.sidebar.code(
    "python -m loaders.load_qualis path/to/qualis.xlsx\n"
    "python -m loaders.load_core   path/to/core.csv\n"
    "python -m loaders.load_sjr    path/to/scimago.csv\n"
    "python -m loaders.load_dblp   123/4567\n"
    "python -m loaders.load_openalex 0000-0000-0000-0000\n"
    "python -m loaders.load_wikicfp 'machine learning'",
    language="bash",
)


# ---------- Views ----------
def view_deadlines() -> None:
    st.header("Upcoming deadlines")
    days = st.slider("Window (days ahead)", 7, 365, 180)
    today = dt.date.today()
    cutoff = today + dt.timedelta(days=days)
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT d.*, v.name AS venue, v.acronym, v.scope,
                   v.qualis, v.core, v.sjr_quartile
            FROM deadlines d JOIN venues v USING(venue_id)
            WHERE (d.paper_due BETWEEN ? AND ?)
               OR (d.abstract_due BETWEEN ? AND ?)
            ORDER BY COALESCE(d.abstract_due, d.paper_due)
            """,
            conn, params=[today, cutoff, today, cutoff],
        )
    finally:
        conn.close()

    if scope_filter:
        df = df[df["scope"].isin(scope_filter)]
    if df.empty:
        st.info("No deadlines in this window. Run loaders or add manually.")
        return
    df["paper_due"] = pd.to_datetime(df["paper_due"])
    df["days_left"] = (df["paper_due"] - pd.Timestamp(today)).dt.days
    cols = ["acronym", "venue", "scope", "qualis", "core",
            "sjr_quartile", "abstract_due", "paper_due", "days_left", "cfp_url"]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)


def view_pipeline() -> None:
    st.header("Submission pipeline")
    df = load_table("submissions")
    venues = load_table("venues")
    if df.empty:
        st.info("No submissions yet. Use 'Add / Edit' to create one.")
        return
    venue_name = (venues.set_index("venue_id")["name"]
                  if not venues.empty else pd.Series(dtype=str))
    df["venue"] = df["venue_id"].map(venue_name).fillna("")
    cols = st.columns(len(PIPELINE_STATUSES))
    for col, status in zip(cols, PIPELINE_STATUSES):
        with col:
            st.subheader(status.replace("_", " "))
            for _, row in df[df["status"] == status].iterrows():
                with st.container(border=True):
                    st.write(f"**{row['title']}**")
                    if row["venue"]:
                        st.caption(row["venue"])


def view_venues() -> None:
    st.header("Venues")
    df = load_table("venues")
    if scope_filter:
        df = df[df["scope"].isin(scope_filter)]

    rolling = df[df["submission_mode"] == "rolling"]
    if not rolling.empty:
        with st.expander(
            f"📖 {len(rolling)} journals open for rolling submission "
            "(fluxo contínuo)",
            expanded=False,
        ):
            st.dataframe(
                rolling[["acronym", "name", "scope", "area",
                         "qualis", "url"]],
                use_container_width=True, hide_index=True,
            )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        qualis = st.multiselect("Qualis",
                                sorted(df["qualis"].dropna().unique().tolist()))
    with c2:
        core = st.multiselect("CORE",
                              sorted(df["core"].dropna().unique().tolist()))
    with c3:
        types = st.multiselect("Type",
                               sorted(df["type"].dropna().unique().tolist()))
    with c4:
        modes = st.multiselect(
            "Submission mode",
            sorted(df["submission_mode"].dropna().unique().tolist()),
        )
    if qualis:
        df = df[df["qualis"].isin(qualis)]
    if core:
        df = df[df["core"].isin(core)]
    if types:
        df = df[df["type"].isin(types)]
    if modes:
        df = df[df["submission_mode"].isin(modes)]
    st.dataframe(df, use_container_width=True, hide_index=True)


def view_stats() -> None:
    st.header("Productivity stats")
    df = load_table("submissions")
    if df.empty:
        st.info("No submissions yet.")
        return
    by_status = df["status"].value_counts().reset_index()
    by_status.columns = ["status", "count"]
    st.plotly_chart(
        px.bar(by_status, x="status", y="count"),
        use_container_width=True,
    )
    decided = df[df["status"].isin(["accepted", "rejected", "published"])]
    if not decided.empty:
        accepted = decided["status"].isin(["accepted", "published"]).sum()
        st.metric(
            "Acceptance rate",
            f"{accepted / len(decided):.0%}",
            help=f"{accepted}/{len(decided)} decided submissions",
        )


def view_add() -> None:
    st.header("Add / Edit")
    tab_sub, tab_ven, tab_dl = st.tabs(
        ["New submission", "New venue", "New deadline"]
    )

    venues = load_table("venues")

    with tab_sub:
        with st.form("new_sub", clear_on_submit=True):
            title = st.text_input("Title")
            venue_id = st.selectbox(
                "Venue",
                options=[None] + venues["venue_id"].tolist(),
                format_func=lambda i: (
                    "(none)" if i is None
                    else venues.loc[venues["venue_id"] == i, "name"].iloc[0]
                ),
            )
            status = st.selectbox("Status", PIPELINE_STATUSES)
            topics = st.text_input("Topics (comma-separated)")
            coauthors = st.text_input("Co-authors")
            notes = st.text_area("Notes")
            if st.form_submit_button("Save") and title:
                conn = get_conn()
                try:
                    conn.execute(
                        """INSERT INTO submissions
                           (title, venue_id, status, topics, coauthors, notes)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (title, venue_id, status, topics, coauthors, notes),
                    )
                    conn.commit()
                finally:
                    conn.close()
                refresh()
                st.success("Saved")

    with tab_ven:
        with st.form("new_venue", clear_on_submit=True):
            name = st.text_input("Name")
            acronym = st.text_input("Acronym")
            type_ = st.selectbox("Type", ["conference", "journal", "workshop"])
            scope = st.selectbox("Scope", ["BR", "INT", "both"])
            area = st.text_input("Area")
            qualis = st.text_input("Qualis (e.g. A1)")
            core = st.text_input("CORE (e.g. A*)")
            sjr = st.text_input("SJR quartile (Q1..Q4)")
            url = st.text_input("URL")
            if st.form_submit_button("Save") and name:
                conn = get_conn()
                try:
                    conn.execute(
                        """INSERT INTO venues
                           (name, acronym, type, scope, area,
                            qualis, core, sjr_quartile, url)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(name, type) DO UPDATE SET
                             acronym=excluded.acronym,
                             scope=excluded.scope,
                             area=excluded.area,
                             qualis=excluded.qualis,
                             core=excluded.core,
                             sjr_quartile=excluded.sjr_quartile,
                             url=excluded.url""",
                        (name, acronym or None, type_, scope, area or None,
                         qualis or None, core or None, sjr or None,
                         url or None),
                    )
                    conn.commit()
                finally:
                    conn.close()
                refresh()
                st.success("Saved")

    with tab_dl:
        if venues.empty:
            st.info("Add a venue first.")
        else:
            with st.form("new_dl", clear_on_submit=True):
                venue_id = st.selectbox(
                    "Venue",
                    options=venues["venue_id"].tolist(),
                    format_func=lambda i: venues.loc[
                        venues["venue_id"] == i, "name"
                    ].iloc[0],
                )
                edition = st.text_input("Edition (e.g. 2026)")
                abstract_due = st.date_input("Abstract due", value=None)
                paper_due = st.date_input("Paper due", value=None)
                notification = st.date_input("Notification", value=None)
                event_start = st.date_input("Event start", value=None)
                location = st.text_input("Location")
                cfp_url = st.text_input("CFP URL")
                if st.form_submit_button("Save"):
                    conn = get_conn()
                    try:
                        conn.execute(
                            """INSERT INTO deadlines
                               (venue_id, edition, abstract_due, paper_due,
                                notification, event_start, location, cfp_url)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (venue_id, edition or None, abstract_due,
                             paper_due, notification, event_start,
                             location or None, cfp_url or None),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    refresh()
                    st.success("Saved")


VIEWS = {
    "Deadlines": view_deadlines,
    "Pipeline": view_pipeline,
    "Venues": view_venues,
    "Stats": view_stats,
    "Add / Edit": view_add,
}
VIEWS[view]()
