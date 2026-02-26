"""
pages/2_Run_Analysis.py
Runs the full SEO analysis pipeline with live progress feedback:
  Phase 1 — Scrape competitor blogs (progress per competitor)
  Phase 2 — Analyse content gaps
  Phase 3 — Generate AI calendar + outlines (progress per outline)
"""

import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime

from utils import (
    load_settings,
    save_settings,
    inject_api_key,
    output_path,
    ensure_output_dir,
    render_sidebar,
    get_global_css,
    enrich_gaps_df,
)

st.set_page_config(
    page_title="Run Analysis - ShipDudes",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Run Analysis")
st.caption(
    "Scrape competitor blogs, identify content gaps, "
    "and generate your 30-day content calendar with AI outlines."
)

settings    = load_settings()
competitors = settings.get("competitors", [])

# ---------------------------------------------------------------------------
# Pre-flight info
# ---------------------------------------------------------------------------
col_a, col_b = st.columns(2)
with col_a:
    st.info(
        f"**{len(competitors)} competitors** configured. "
        "Edit on the Competitors page."
    )
with col_b:
    st.info(
        "Expected runtime: **5–10 minutes** "
        "(scraping + 30 AI outline calls)."
    )

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
st.subheader("Options")
run_calendar = st.checkbox(
    "Generate AI content calendar and outlines (uses Anthropic API)",
    value=True,
    help="Uncheck to only scrape and analyse gaps without the AI step — faster and free.",
)

if run_calendar:
    inject_api_key()
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning(
            "ANTHROPIC_API_KEY not found. "
            "Add it to `.streamlit/secrets.toml` (local) or the Streamlit Cloud Secrets dashboard."
        )

st.divider()

# ---------------------------------------------------------------------------
# Run button
# ---------------------------------------------------------------------------
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False

start_btn = st.button(
    "Start Analysis",
    type="primary",
    disabled=st.session_state.analysis_running,
    use_container_width=False,
)

if start_btn:
    if not competitors:
        st.error("No competitors configured. Add some on the Competitors page first.")
        st.stop()

    st.session_state.analysis_running = True
    ensure_output_dir()

    # -----------------------------------------------------------------------
    # PHASE 1: Scrape
    # -----------------------------------------------------------------------
    st.subheader("Phase 1 — Scraping Competitor Blogs")

    phase1_progress = st.progress(0.0, text="Starting scraper...")
    phase1_log      = st.container()

    from scraper import scrape_competitor

    all_results  = []
    total_comps  = len(competitors)
    scraped_comp_count = 0

    for i, comp in enumerate(competitors):
        phase1_progress.progress(
            i / total_comps,
            text=f"Scraping {comp['name']}... ({i + 1}/{total_comps})",
        )
        posts = scrape_competitor(comp)
        all_results.extend(posts)
        scraped_comp_count += 1

        with phase1_log:
            if posts:
                st.success(f"**{comp['name']}** — {len(posts)} posts scraped")
            else:
                st.warning(f"**{comp['name']}** — no posts found (site may block scrapers)")

        phase1_progress.progress(
            (i + 1) / total_comps,
            text=f"Done: {comp['name']}",
        )

    phase1_progress.progress(1.0, text="Scraping complete")

    if not all_results:
        st.error(
            "No data was scraped from any competitor. "
            "Check the URLs on the Competitors page and your internet connection."
        )
        st.session_state.analysis_running = False
        st.stop()

    st.success(
        f"Phase 1 complete — **{len(all_results)} posts** collected "
        f"from **{scraped_comp_count}** competitors."
    )

    # -----------------------------------------------------------------------
    # PHASE 2: Analyse
    # -----------------------------------------------------------------------
    st.subheader("Phase 2 — Analysing Content Gaps")

    with st.spinner("Classifying posts into topic clusters..."):
        from analyzer import find_content_gaps, get_raw_titles_for_ai

        competitor_df = pd.DataFrame(all_results)
        competitor_df.drop(columns=["_all_headings"], errors="ignore").to_csv(
            output_path("competitor_data.csv"), index=False
        )

        gaps_df          = find_content_gaps(competitor_df)
        competitor_titles = get_raw_titles_for_ai(competitor_df)

        if not gaps_df.empty:
            gaps_df.to_csv(output_path("content_gaps.csv"), index=False)

    if gaps_df.empty:
        st.warning("No content gaps identified — all topics may already be covered.")
    else:
        st.success(f"Phase 2 complete — **{len(gaps_df)} topic clusters** identified.")

        top5 = enrich_gaps_df(gaps_df).head(5)[
            ["topic", "competitor_count", "CPG/DTC Relevance", "AI Visibility"]
        ]
        st.dataframe(top5, use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------
    # PHASE 3: AI Calendar
    # -----------------------------------------------------------------------
    if run_calendar:
        st.subheader("Phase 3 — Generating AI Content Calendar")

        from calendar_generator import (
            generate_content_calendar,
            generate_outline,
            _client,
            _publish_dates,
            _build_markdown,
        )
        from config import CALENDAR_SETTINGS

        phase3_progress = st.progress(0.0, text="Connecting to Claude...")

        try:
            client = _client()
        except ValueError as e:
            st.error(str(e))
            st.session_state.analysis_running = False
            st.stop()

        # Step 3a: generate calendar plan
        with st.spinner("Planning 30 post ideas..."):
            calendar_items = generate_content_calendar(gaps_df, competitor_titles)

        # Assign publish dates
        pub_dates = _publish_dates(
            total=len(calendar_items),
            posts_per_week=CALENDAR_SETTINGS.get("posts_per_week", 3),
            start=CALENDAR_SETTINGS.get("start_date"),
        )

        # Step 3b: generate outlines
        with st.status("Generating 30 blog post outlines with Claude...", expanded=True) as gen_status:
            for i, post in enumerate(calendar_items):
                pub = pub_dates[i] if i < len(pub_dates) else None
                post["publish_date"] = pub.strftime("%Y-%m-%d") if pub else ""
                post["day_of_week"]  = pub.strftime("%A")       if pub else ""

                st.write(f"[{i + 1:02d}/30] {post['title'][:70]}")

                try:
                    post["outline"] = generate_outline(post, client)
                except Exception as e:
                    post["outline"] = f"_Generation failed: {e}_"

                phase3_progress.progress(
                    (i + 1) / len(calendar_items),
                    text=f"Outline {i + 1}/{len(calendar_items)} done",
                )

            gen_status.update(label="All 30 outlines generated!", state="complete")

        # Save outputs
        calendar_df = pd.DataFrame(calendar_items)

        # CSV (no outline column — for spreadsheet use)
        csv_cols = [
            "post_number", "publish_date", "day_of_week", "title",
            "primary_keyword", "topic_cluster", "funnel_stage",
            "content_type", "brief",
        ]
        keep = [c for c in csv_cols if c in calendar_df.columns]
        calendar_df[keep].to_csv(output_path("content_calendar.csv"), index=False)

        # Full JSON (with outlines — for the calendar page)
        with open(output_path("calendar_full.json"), "w", encoding="utf-8") as f:
            json.dump(calendar_items, f, indent=2, ensure_ascii=False)

        # Markdown report
        markdown = _build_markdown(calendar_df, gaps_df)
        with open(output_path("content_plan.md"), "w", encoding="utf-8") as f:
            f.write(markdown)

        st.success("Phase 3 complete — content calendar saved.")

    # -----------------------------------------------------------------------
    # Update stats and finish
    # -----------------------------------------------------------------------
    posts_generated = len(calendar_items) if run_calendar else 0

    settings["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    settings["last_run_stats"] = {
        "posts_scraped":     len(all_results),
        "gaps_found":        len(gaps_df) if not gaps_df.empty else 0,
        "posts_generated":   posts_generated,
        "competitors_scraped": scraped_comp_count,
    }
    save_settings(settings)
    st.session_state.analysis_running = False

    st.balloons()
    st.success(
        "Analysis complete! Use the sidebar to navigate to "
        "**Opportunities** or **Content Calendar**."
    )
