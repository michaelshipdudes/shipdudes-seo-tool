"""
streamlit_app.py
Home Dashboard — entry point for the ShipDudes SEO Content Intelligence Tool.
"""

import os
import streamlit as st
import pandas as pd

from utils import (
    load_settings,
    render_sidebar,
    output_exists,
    output_path,
    get_global_css,
    enrich_gaps_df,
)

st.set_page_config(
    page_title="ShipDudes - SEO Tool",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_global_css(), unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Dashboard")
st.caption("Your ShipDudes SEO content pipeline at a glance.")

settings   = load_settings()
last_run   = settings.get("last_run")
stats      = settings.get("last_run_stats", {})
competitors = settings.get("competitors", [])

# ---------------------------------------------------------------------------
# Quick stats row
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Competitors Tracked",  len(competitors))
c2.metric("Posts Scraped",        stats.get("posts_scraped",    "—"))
c3.metric("Content Gaps Found",   stats.get("gaps_found",       "—"))
c4.metric("Calendar Posts",       stats.get("posts_generated",  "—"))

st.divider()

# ---------------------------------------------------------------------------
# Status + primary CTA
# ---------------------------------------------------------------------------
if not output_exists("content_calendar.csv"):
    st.info(
        "No analysis data yet. Head to **Run Analysis** to scrape competitors "
        "and generate your content calendar."
    )
    if st.button("Go to Run Analysis →", type="primary"):
        st.switch_page("pages/2_Run_Analysis.py")
else:
    st.success(f"Last analysis completed: **{last_run}**")

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("Run New Analysis", type="primary", use_container_width=True):
            st.switch_page("pages/2_Run_Analysis.py")
    with btn2:
        if st.button("View Content Calendar", use_container_width=True):
            st.switch_page("pages/4_Content_Calendar.py")
    with btn3:
        if st.button("View Opportunities", use_container_width=True):
            st.switch_page("pages/3_Opportunities.py")

# ---------------------------------------------------------------------------
# Top opportunities preview
# ---------------------------------------------------------------------------
if output_exists("content_gaps.csv"):
    st.subheader("Top Content Opportunities")
    df = pd.read_csv(output_path("content_gaps.csv"))
    df = enrich_gaps_df(df)

    preview = df.head(8)[
        ["topic", "competitor_count", "post_count", "CPG/DTC Relevance", "AI Visibility"]
    ].rename(columns={
        "topic":            "Topic",
        "competitor_count": "Competitors",
        "post_count":       "Posts",
    })

    st.dataframe(
        preview,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Competitors": st.column_config.NumberColumn(width="small"),
            "Posts":        st.column_config.NumberColumn(width="small"),
        },
    )
    st.caption("Full sortable table on the Opportunities page.")

# ---------------------------------------------------------------------------
# Getting started guide (shown until first run)
# ---------------------------------------------------------------------------
if not output_exists("content_gaps.csv"):
    st.divider()
    st.subheader("Getting Started")

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
**1. Configure Competitors**
Go to the **Competitors** page to review or update the list of competitor blogs
to scrape. ShipBob, ShipMonk, Red Stag, and others are pre-loaded.
        """)
    with s2:
        st.markdown("""
**2. Run Analysis**
Hit **Run Analysis** to scrape competitor blogs, identify content gaps,
and generate 30 AI-written blog post outlines via the Anthropic API.
        """)
    with s3:
        st.markdown("""
**3. Write & Publish**
Review your **Content Calendar** for outlines, check **Opportunities**
for priority topics, and **Export** your files to start writing on Framer.
        """)
