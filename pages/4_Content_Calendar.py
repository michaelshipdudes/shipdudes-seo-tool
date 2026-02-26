"""
pages/4_Content_Calendar.py
Visual 7-column week grid calendar.
Click any scheduled post to expand its full AI-generated outline.
"""

import json
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils import (
    render_sidebar,
    get_global_css,
    output_exists,
    output_path,
)

st.set_page_config(
    page_title="Content Calendar - ShipDudes",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Calendar-specific CSS
# ---------------------------------------------------------------------------
CALENDAR_CSS = """
<style>
/* Post day buttons — look like calendar tiles */
div[data-testid="column"] div[data-testid="stButton"] button {
    background-color: #162236 !important;
    border: 1px solid #2A4060 !important;
    border-left: 3px solid #FF6B35 !important;
    color: #E8EDF2 !important;
    text-align: left !important;
    min-height: 72px !important;
    font-size: 0.70rem !important;
    white-space: pre-wrap !important;
    padding: 6px 8px !important;
    border-radius: 6px !important;
    line-height: 1.35 !important;
}
div[data-testid="column"] div[data-testid="stButton"] button:hover {
    border-color: #FF6B35 !important;
    background-color: #1E3A5F !important;
}
div[data-testid="column"] div[data-testid="stButton"] button[kind="primary"] {
    background-color: #1E3A5F !important;
    border-color: #FF6B35 !important;
    border-width: 2px !important;
}
/* Day-name header row */
.cal-header {
    text-align: center;
    color: #8BA3BF;
    font-weight: 600;
    font-size: 0.78rem;
    padding: 4px 0 6px 0;
    letter-spacing: 0.04em;
}
/* Empty day cell */
.cal-empty {
    background-color: #111E2E;
    border: 1px solid #1B2D45;
    border-radius: 6px;
    min-height: 72px;
    display: flex;
    align-items: flex-start;
    padding: 6px 8px;
    color: #2A3F5F;
    font-size: 0.75rem;
}
/* Month label above each week */
.week-label {
    color: #8BA3BF;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 12px 0 4px 0;
}
/* Outline panel */
.outline-panel {
    background-color: #1B2D45;
    border-left: 4px solid #FF6B35;
    border-radius: 0 10px 10px 0;
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}
</style>
"""

st.markdown(get_global_css() + CALENDAR_CSS, unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Content Calendar")
st.caption(
    "30-day posting schedule on a Mon / Wed / Fri cadence. "
    "Click any post tile to read its full outline."
)

# ---------------------------------------------------------------------------
# Gate: needs data
# ---------------------------------------------------------------------------
if not output_exists("calendar_full.json"):
    # Fall back to CSV-only if full JSON not yet generated
    if not output_exists("content_calendar.csv"):
        st.info("No calendar data found. Run Analysis first.")
        if st.button("Go to Run Analysis", type="primary"):
            st.switch_page("pages/2_Run_Analysis.py")
        st.stop()
    else:
        st.warning(
            "Full outline data (`calendar_full.json`) not found — "
            "outlines will not be shown. Re-run analysis to generate them."
        )

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
posts      = []
has_outlines = False

if output_exists("calendar_full.json"):
    with open(output_path("calendar_full.json"), encoding="utf-8") as f:
        posts = json.load(f)
    has_outlines = True
elif output_exists("content_calendar.csv"):
    df = pd.read_csv(output_path("content_calendar.csv"))
    posts = df.to_dict(orient="records")

# Build date → post lookup
posts_by_date = {}
for p in posts:
    d = p.get("publish_date", "")
    if d:
        posts_by_date[d] = p

# ---------------------------------------------------------------------------
# Session state for selected post
# ---------------------------------------------------------------------------
if "cal_selected" not in st.session_state:
    st.session_state.cal_selected = None

# ---------------------------------------------------------------------------
# Date range
# ---------------------------------------------------------------------------
valid_dates = [
    date.fromisoformat(p["publish_date"])
    for p in posts
    if p.get("publish_date")
]
if not valid_dates:
    st.error("No publish dates found in the calendar data.")
    st.stop()

min_date = min(valid_dates)
max_date = max(valid_dates)

# Snap to Monday of first week and Sunday of last week
grid_start = min_date - timedelta(days=min_date.weekday())
grid_end   = max_date + timedelta(days=6 - max_date.weekday())

# ---------------------------------------------------------------------------
# Stats row
# ---------------------------------------------------------------------------
s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Posts",         len(posts))
s2.metric("Weeks Covered",       ((grid_end - grid_start).days + 1) // 7)
s3.metric("First Post",          min_date.strftime("%b %d"))
s4.metric("Last Post",           max_date.strftime("%b %d"))

st.divider()

# ---------------------------------------------------------------------------
# Day-name header row
# ---------------------------------------------------------------------------
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FUNNEL_ICON = {"awareness": "💡", "consideration": "🔍", "decision": "✅"}

header_cols = st.columns(7)
for i, name in enumerate(DAY_NAMES):
    with header_cols[i]:
        st.markdown(f"<div class='cal-header'>{name}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Week rows
# ---------------------------------------------------------------------------
current_week_start = grid_start

while current_week_start <= grid_end:
    week_label = current_week_start.strftime("%B %d")
    st.markdown(f"<div class='week-label'>Week of {week_label}</div>", unsafe_allow_html=True)

    day_cols = st.columns(7)

    for i in range(7):
        day = current_week_start + timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        post     = posts_by_date.get(date_str)

        with day_cols[i]:
            if post:
                num    = post.get("post_number", "?")
                title  = post.get("title", "Untitled")
                stage  = post.get("funnel_stage", "")
                icon   = FUNNEL_ICON.get(stage, "")
                label  = f"#{num} {icon}\n{title[:45]}{'...' if len(title) > 45 else ''}"

                is_selected = (
                    st.session_state.cal_selected is not None and
                    st.session_state.cal_selected.get("post_number") == num
                )

                if st.button(
                    label,
                    key=f"cal_{date_str}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    if is_selected:
                        st.session_state.cal_selected = None
                    else:
                        st.session_state.cal_selected = post
                    st.rerun()
            else:
                day_num = str(day.day)
                st.markdown(
                    f"<div class='cal-empty'>{day_num}</div>",
                    unsafe_allow_html=True,
                )

    current_week_start += timedelta(weeks=1)

# ---------------------------------------------------------------------------
# Selected post outline panel
# ---------------------------------------------------------------------------
if st.session_state.cal_selected:
    post = st.session_state.cal_selected
    st.divider()

    pub   = post.get("publish_date", "")
    dow   = post.get("day_of_week", "")
    num   = post.get("post_number", "?")
    stage = post.get("funnel_stage", "")

    st.markdown(
        f"<div class='outline-panel'>"
        f"<strong style='color:#FF6B35;font-size:0.8rem;text-transform:uppercase;"
        f"letter-spacing:0.06em;'>Post #{num}  •  {dow} {pub}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    meta1, meta2, meta3, meta4 = st.columns(4)
    meta1.markdown(f"**Title**  \n{post.get('title', '—')}")
    meta2.markdown(f"**Primary Keyword**  \n{post.get('primary_keyword', '—')}")
    meta3.markdown(f"**Topic Cluster**  \n{post.get('topic_cluster', '—')}")
    meta4.markdown(
        f"**Funnel Stage**  \n"
        f"{FUNNEL_ICON.get(stage, '')} {stage.capitalize() if stage else '—'}"
    )

    if post.get("brief"):
        st.markdown(f"> {post['brief']}")

    if has_outlines and post.get("outline"):
        st.markdown("---")
        st.markdown(post["outline"])
    elif not has_outlines:
        st.info("Re-run Analysis with AI calendar enabled to generate outlines.")

    if st.button("Close outline", type="secondary"):
        st.session_state.cal_selected = None
        st.rerun()

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
with st.expander("Legend"):
    st.markdown(
        "💡 **Awareness** — educational content for people new to 3PL / fulfillment  \n"
        "🔍 **Consideration** — comparison and how-to content for brands evaluating options  \n"
        "✅ **Decision** — bottom-funnel content for brands ready to choose ShipDudes"
    )
