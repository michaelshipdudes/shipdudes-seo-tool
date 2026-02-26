"""
main.py
Entry point — runs the full ShipDudes SEO content pipeline:
  1. Scrape competitor blogs
  2. Analyse content gaps
  3. Generate 30-day calendar + outlines via Anthropic API
  4. Save everything to output/
"""

import os
import sys
import pandas as pd

from scraper import scrape_all_competitors
from analyzer import find_content_gaps, get_raw_titles_for_ai
from calendar_generator import build_full_calendar

OUTPUT_DIR = "output"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_outputs(competitor_df, gaps_df, calendar_df, markdown):
    ensure_output_dir()

    # 1. Raw competitor data (drop internal-only column)
    competitor_path = os.path.join(OUTPUT_DIR, "competitor_data.csv")
    competitor_df.drop(columns=["_all_headings"], errors="ignore").to_csv(
        competitor_path, index=False
    )
    print(f"  Saved -> {competitor_path}")

    # 2. Content gap analysis
    if not gaps_df.empty:
        gaps_path = os.path.join(OUTPUT_DIR, "content_gaps.csv")
        gaps_df.to_csv(gaps_path, index=False)
        print(f"  Saved -> {gaps_path}")

    # 3. Content calendar (schedule view — no outlines)
    if not calendar_df.empty:
        csv_cols = [
            "post_number", "publish_date", "day_of_week",
            "title", "primary_keyword", "topic_cluster",
            "funnel_stage", "content_type", "brief",
        ]
        keep = [c for c in csv_cols if c in calendar_df.columns]
        cal_path = os.path.join(OUTPUT_DIR, "content_calendar.csv")
        calendar_df[keep].to_csv(cal_path, index=False)
        print(f"  Saved -> {cal_path}")

    # 4. Full markdown report (calendar + outlines)
    md_path = os.path.join(OUTPUT_DIR, "content_plan.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  Saved -> {md_path}")


def main():
    print("=" * 60)
    print("  ShipDudes SEO Content Tool")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Scrape competitor blogs
    # ------------------------------------------------------------------
    print("\n[Step 1/3] Scraping competitor blogs ...")
    competitor_df = scrape_all_competitors()

    if competitor_df.empty:
        print(
            "\n[FATAL] No competitor data scraped.\n"
            "Check your internet connection and the URLs in config.py."
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: Analyse content gaps
    # ------------------------------------------------------------------
    print("\n[Step 2/3] Analysing content gaps ...")
    gaps_df = find_content_gaps(competitor_df)
    competitor_titles = get_raw_titles_for_ai(competitor_df)

    # ------------------------------------------------------------------
    # Step 3: Generate content calendar + outlines
    # ------------------------------------------------------------------
    print("\n[Step 3/3] Generating 30-day calendar and outlines with Claude ...")
    calendar_df, markdown = build_full_calendar(gaps_df, competitor_titles)

    # ------------------------------------------------------------------
    # Save everything
    # ------------------------------------------------------------------
    print("\n[Saving outputs ...]")
    save_outputs(competitor_df, gaps_df, calendar_df, markdown)

    print("\n" + "=" * 60)
    print("  All done! Your files are in the output/ folder:")
    print("    competitor_data.csv   - raw scrape results")
    print("    content_gaps.csv      - gap analysis by topic cluster")
    print("    content_calendar.csv  - 30-day schedule (no outlines)")
    print("    content_plan.md       - full report with all outlines")
    print("=" * 60)


if __name__ == "__main__":
    main()
