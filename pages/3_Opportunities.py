"""
pages/3_Opportunities.py
Sortable, filterable table of content gap topics with rule-based
CPG/DTC Relevance and AI Visibility labels.
"""

import streamlit as st
import pandas as pd

from utils import (
    render_sidebar,
    get_global_css,
    output_exists,
    output_path,
    enrich_gaps_df,
)

st.set_page_config(
    page_title="Opportunities - ShipDudes",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Content Opportunities")
st.caption(
    "Topics your competitors rank for that ShipDudes has zero coverage on — "
    "ranked by competitor breadth and post volume."
)

if not output_exists("content_gaps.csv"):
    st.info("No gap data found. Run Analysis first to generate opportunities.")
    if st.button("Go to Run Analysis", type="primary"):
        st.switch_page("pages/2_Run_Analysis.py")
    st.stop()

# ---------------------------------------------------------------------------
# Load and enrich data
# ---------------------------------------------------------------------------
df = pd.read_csv(output_path("content_gaps.csv"))
df = enrich_gaps_df(df)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Filters")

    max_competitors = int(df["competitor_count"].max()) if not df.empty else 6
    min_comp = st.slider(
        "Min. competitors covering topic",
        min_value=1,
        max_value=max_competitors,
        value=1,
    )

    relevance_opts = st.multiselect(
        "CPG/DTC Relevance",
        options=["High", "Medium", "Low"],
        default=["High", "Medium"],
    )

    ai_opts = st.multiselect(
        "AI Visibility",
        options=["High", "Medium", "Low"],
        default=["High", "Medium"],
    )

    st.divider()
    st.caption(
        "**CPG/DTC Relevance** — how directly the topic speaks to "
        "CPG operators and DTC brands.\n\n"
        "**AI Visibility** — likelihood that AI tools (ChatGPT, Claude, Gemini) "
        "will cite content on this topic when answering user questions."
    )

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
rel_filter = relevance_opts if relevance_opts else ["High", "Medium", "Low"]
ai_filter  = ai_opts        if ai_opts        else ["High", "Medium", "Low"]

filtered = df[
    (df["competitor_count"]    >= min_comp) &
    (df["CPG/DTC Relevance"].isin(rel_filter)) &
    (df["AI Visibility"].isin(ai_filter))
].copy()

# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Opportunities",  len(df))
m2.metric("Filtered Results",     len(filtered))
m3.metric("High CPG/DTC Relevance", len(filtered[filtered["CPG/DTC Relevance"] == "High"]))
m4.metric("High AI Visibility",   len(filtered[filtered["AI Visibility"]     == "High"]))

st.divider()

# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------
if filtered.empty:
    st.warning("No topics match the current filters. Try widening your selections.")
else:
    display = filtered[[
        "topic",
        "competitor_count",
        "post_count",
        "CPG/DTC Relevance",
        "AI Visibility",
        "competitors_covering",
        "example_posts",
    ]].rename(columns={
        "topic":                "Topic",
        "competitor_count":     "Competitors",
        "post_count":           "Posts",
        "competitors_covering": "Covered By",
        "example_posts":        "Example Posts",
    })

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Topic":            st.column_config.TextColumn(width="medium"),
            "Competitors":      st.column_config.NumberColumn(
                                    width="small",
                                    help="Number of tracked competitors with posts on this topic",
                                ),
            "Posts":            st.column_config.NumberColumn(
                                    width="small",
                                    help="Total posts on this topic across all competitors",
                                ),
            "CPG/DTC Relevance": st.column_config.TextColumn(width="small"),
            "AI Visibility":    st.column_config.TextColumn(width="small"),
            "Covered By":       st.column_config.TextColumn(width="medium"),
            "Example Posts":    st.column_config.TextColumn(width="large"),
        },
    )

    st.caption(
        "Click any column header to sort. "
        "All columns are sortable."
    )

# ---------------------------------------------------------------------------
# Topic detail expander
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Topic Detail")
st.caption("Select a topic to see competitor example posts for that cluster.")

topic_names = filtered["topic"].tolist() if not filtered.empty else []
if topic_names:
    selected_topic = st.selectbox("Select topic", options=topic_names)
    row = filtered[filtered["topic"] == selected_topic].iloc[0]

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        st.markdown(f"**Topic:** {row['topic']}")
        st.markdown(f"**Competitor coverage:** {row['competitor_count']} competitors, {row['post_count']} posts")
        st.markdown(f"**Covered by:** {row['competitors_covering']}")
        st.markdown(f"**CPG/DTC Relevance:** {row['CPG/DTC Relevance']}")
        st.markdown(f"**AI Visibility:** {row['AI Visibility']}")

    with detail_col2:
        st.markdown("**Example competitor posts:**")
        examples = str(row.get("example_posts", "")).split(" || ")
        for ex in examples:
            if ex.strip():
                st.markdown(f"- {ex.strip()}")
