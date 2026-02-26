"""
pages/5_Export.py
Download all generated output files with a single click.
"""

import streamlit as st

from utils import (
    render_sidebar,
    get_global_css,
    output_exists,
    output_path,
)

st.set_page_config(
    page_title="Export - ShipDudes",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Export")
st.caption(
    "Download your content plan files. "
    "All files are generated during Run Analysis."
)

# ---------------------------------------------------------------------------
# File manifest
# ---------------------------------------------------------------------------
EXPORT_FILES = [
    {
        "filename": "content_plan.md",
        "label":    "Full Content Plan",
        "ext":      "Markdown",
        "desc":     (
            "Complete 30-day content plan with all blog post outlines. "
            "Open in any markdown editor or paste into Notion / Framer."
        ),
        "mime":     "text/markdown",
        "icon":     "📝",
    },
    {
        "filename": "content_calendar.csv",
        "label":    "Content Calendar",
        "ext":      "CSV",
        "desc":     (
            "30-day posting schedule: title, primary keyword, topic cluster, "
            "funnel stage, publish date. Import to Google Sheets or Airtable."
        ),
        "mime":     "text/csv",
        "icon":     "📅",
    },
    {
        "filename": "content_gaps.csv",
        "label":    "Content Opportunities",
        "ext":      "CSV",
        "desc":     (
            "Topic gap analysis ranked by competitor coverage and priority score. "
            "Includes CPG/DTC Relevance and AI Visibility ratings."
        ),
        "mime":     "text/csv",
        "icon":     "🎯",
    },
    {
        "filename": "competitor_data.csv",
        "label":    "Competitor Scrape Data",
        "ext":      "CSV",
        "desc":     (
            "Raw data from competitor blogs: page titles, meta descriptions, "
            "H1–H3 headings per post. Useful for manual research."
        ),
        "mime":     "text/csv",
        "icon":     "🔗",
    },
    {
        "filename": "calendar_full.json",
        "label":    "Calendar Full Data",
        "ext":      "JSON",
        "desc":     (
            "Complete calendar data including outlines in JSON format. "
            "Useful for importing into custom tools or databases."
        ),
        "mime":     "application/json",
        "icon":     "🗂️",
    },
]

any_ready = any(output_exists(f["filename"]) for f in EXPORT_FILES)

if not any_ready:
    st.info("No files to export yet. Run Analysis first to generate your content plan.")
    if st.button("Go to Run Analysis", type="primary"):
        st.switch_page("pages/2_Run_Analysis.py")
    st.stop()

# ---------------------------------------------------------------------------
# Export cards
# ---------------------------------------------------------------------------
for file_info in EXPORT_FILES:
    ready = output_exists(file_info["filename"])

    with st.container():
        left, right = st.columns([6, 1])

        with left:
            status_dot = "🟢" if ready else "⚪"
            st.markdown(
                f"{status_dot} **{file_info['icon']} {file_info['label']}** "
                f"<span style='color:#8BA3BF;font-size:0.8rem;'>— {file_info['ext']}</span>",
                unsafe_allow_html=True,
            )
            st.caption(file_info["desc"])

        with right:
            st.markdown("<div style='padding-top:0.4rem;'>", unsafe_allow_html=True)
            if ready:
                with open(output_path(file_info["filename"]), "rb") as fh:
                    st.download_button(
                        label="Download",
                        data=fh.read(),
                        file_name=file_info["filename"],
                        mime=file_info["mime"],
                        use_container_width=True,
                        key=f"dl_{file_info['filename']}",
                    )
            else:
                st.button(
                    "Not ready",
                    disabled=True,
                    use_container_width=True,
                    key=f"nr_{file_info['filename']}",
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

# ---------------------------------------------------------------------------
# Bulk download tip
# ---------------------------------------------------------------------------
ready_count = sum(1 for f in EXPORT_FILES if output_exists(f["filename"]))
st.caption(
    f"{ready_count}/{len(EXPORT_FILES)} files ready to download. "
    "Re-run Analysis at any time to refresh all files with updated competitor data."
)
