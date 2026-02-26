"""
calendar_generator.py
Uses the Anthropic API to:
  1. Generate a prioritised 30-post content calendar from gap analysis data.
  2. Generate a detailed outline for each post.
  3. Assemble everything into a DataFrame and a markdown report.
"""

import os
import re
import json
import anthropic
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv

from config import CALENDAR_SETTINGS, SHIPDUDES_CONTEXT, AI_MODEL

load_dotenv()


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def _client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. "
            "Copy .env.example to .env and add your key."
        )
    return anthropic.Anthropic(api_key=api_key)


def _call(client, prompt, max_tokens=8000):
    """Single wrapper around client.messages.create."""
    msg = client.messages.create(
        model=AI_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


# ---------------------------------------------------------------------------
# Publishing schedule
# ---------------------------------------------------------------------------

def _publish_dates(total, posts_per_week=3, start=None):
    """
    Return a list of `total` dates on a Mon/Wed/Fri schedule.
    `start` defaults to today.
    """
    if start is None:
        start = date.today()

    publish_weekdays = {0, 2, 4}   # Mon=0, Wed=2, Fri=4
    dates = []
    current = start

    while len(dates) < total:
        if current.weekday() in publish_weekdays:
            dates.append(current)
        current += timedelta(days=1)

    return dates


# ---------------------------------------------------------------------------
# Step 1: Generate the 30-post content calendar
# ---------------------------------------------------------------------------

def generate_content_calendar(gap_topics_df, competitor_titles):
    """
    Ask Claude to produce a 30-post calendar in JSON format.
    Returns a list of dicts (one per post).
    """
    print("\n[AI] Generating 30-post content calendar ...")
    client = _client()

    topics_block = ""
    if not gap_topics_df.empty:
        for _, row in gap_topics_df.iterrows():
            topics_block += (
                f"- {row['topic']} "
                f"(covered by {row['competitor_count']} competitors, "
                f"{row['post_count']} posts)\n"
            )

    titles_block = "\n".join(f"- {t}" for t in competitor_titles[:40])

    prompt = f"""You are an SEO content strategist for ShipDudes, a 3PL ecommerce fulfillment company.

BUSINESS CONTEXT:
{SHIPDUDES_CONTEXT}

CONTENT GAPS — topics competitors rank for that ShipDudes has zero coverage on:
{topics_block}

SAMPLE COMPETITOR POST TITLES (reference only — do NOT copy verbatim):
{titles_block}

TASK:
Create exactly 30 unique blog post ideas for ShipDudes that:
1. Target CPG operators and DTC brands searching for 3PL / fulfillment solutions
2. Span all funnel stages: awareness (educational), consideration (comparison/how-to), decision (why ShipDudes)
3. Mix content types: how-to guides, listicles, comparisons, data-driven pieces, case study angles
4. Target keywords that help ShipDudes rank on Google AND get cited by AI tools like ChatGPT, Claude, Gemini
5. Add a ShipDudes angle — not generic logistics posts but posts that speak to their ideal customer

Return ONLY a valid JSON array with exactly 30 objects. Each object must have these exact keys:
- "post_number"    : integer 1-30
- "title"          : SEO-optimised blog post title (compelling, keyword-rich)
- "primary_keyword": the single main keyword to target
- "topic_cluster"  : the topic category from the gap list (or a new one if needed)
- "funnel_stage"   : one of "awareness", "consideration", or "decision"
- "content_type"   : e.g. "How-To Guide", "Listicle", "Comparison", "Educational", "Case Study Angle"
- "brief"          : 1-2 sentences describing what this post must cover and why it matters to ShipDudes' customer

Return ONLY the raw JSON array. No markdown fences, no explanation."""

    raw = _call(client, prompt, max_tokens=8000)

    # Strip any accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    calendar_items = json.loads(raw)
    print(f"[AI] Calendar generated — {len(calendar_items)} posts planned")
    return calendar_items


# ---------------------------------------------------------------------------
# Step 2: Generate one outline per post
# ---------------------------------------------------------------------------

def generate_outline(post, client):
    """
    Ask Claude to produce a detailed markdown outline for a single post.
    Returns a markdown string.
    """
    prompt = f"""You are an SEO content strategist for ShipDudes, a 3PL ecommerce fulfillment company.

BUSINESS CONTEXT:
{SHIPDUDES_CONTEXT}

Generate a detailed blog post outline for:
- Title          : {post["title"]}
- Primary Keyword: {post["primary_keyword"]}
- Topic Cluster  : {post["topic_cluster"]}
- Funnel Stage   : {post["funnel_stage"]}
- Content Type   : {post["content_type"]}
- Brief          : {post["brief"]}

Requirements for the outline:
- Use H2 headings for each major section (4-7 sections depending on content type)
- Under each H2, include 3-5 bullet points describing exactly what to write
- Include a suggested word count (aim for 800-1400 words)
- Include 2-3 internal linking suggestions (other topics ShipDudes should eventually cover)
- End with a clear CTA (call to action) section aligned to the funnel stage
- Prioritise practical, specific advice over fluff — this audience is operators, not beginners

Start directly with the outline. No preamble."""

    return _call(client, prompt, max_tokens=1500)


# ---------------------------------------------------------------------------
# Step 3: Orchestrate everything
# ---------------------------------------------------------------------------

def build_full_calendar(gap_topics_df, competitor_titles):
    """
    Full pipeline:
      1. Generate 30 post ideas with Claude
      2. Assign Mon/Wed/Fri publish dates
      3. Generate a detailed outline for each post
      4. Return (calendar_df, markdown_string)
    """
    client = _client()

    # 1. Calendar
    calendar_items = generate_content_calendar(gap_topics_df, competitor_titles)

    # 2. Assign publish dates
    publish_dates = _publish_dates(
        total=len(calendar_items),
        posts_per_week=CALENDAR_SETTINGS.get("posts_per_week", 3),
        start=CALENDAR_SETTINGS.get("start_date"),
    )

    # 3. Outlines
    print(f"\n[AI] Generating {len(calendar_items)} outlines (this takes ~2 min) ...")
    enriched = []

    for i, post in enumerate(calendar_items, 1):
        pub = publish_dates[i - 1] if i <= len(publish_dates) else None
        post["publish_date"] = pub.strftime("%Y-%m-%d") if pub else ""
        post["day_of_week"]  = pub.strftime("%A") if pub else ""

        print(f"  [{i:02d}/{len(calendar_items)}] {post['title'][:65]}")
        try:
            post["outline"] = generate_outline(post, client)
        except Exception as e:
            print(f"    [ERROR] Outline failed: {e}")
            post["outline"] = "_Outline generation failed — re-run for this post._"

        enriched.append(post)

    # 4. Build outputs
    calendar_df = pd.DataFrame(enriched)
    markdown    = _build_markdown(calendar_df, gap_topics_df)

    return calendar_df, markdown


# ---------------------------------------------------------------------------
# Markdown report builder
# ---------------------------------------------------------------------------

def _build_markdown(calendar_df, gap_topics_df):
    today_str = date.today().strftime("%B %d, %Y")

    lines = [
        "# ShipDudes 30-Day Content Plan",
        f"*Generated: {today_str}*",
        "",
        "---",
        "",
        "## Content Gap Analysis Summary",
        "",
        "Topics competitors rank for that ShipDudes has zero coverage on, ranked by opportunity:",
        "",
    ]

    if not gap_topics_df.empty:
        lines.append("| Topic | Competitors | Posts |")
        lines.append("|-------|-------------|-------|")
        for _, r in gap_topics_df.iterrows():
            lines.append(f"| {r['topic']} | {r['competitor_count']} | {r['post_count']} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## 30-Day Content Calendar",
        "",
        "> **Publishing cadence:** Monday / Wednesday / Friday — 3 posts per week",
        "",
    ]

    current_week_label = None
    week_num = 0

    for _, row in calendar_df.iterrows():
        pub_date = row.get("publish_date", "")

        # Derive week label
        if pub_date:
            from datetime import date as _date
            dt = _date.fromisoformat(pub_date)
            week_start = dt - timedelta(days=dt.weekday())
            week_label = f"Week of {week_start.strftime('%B %d, %Y')}"
        else:
            week_label = "Unscheduled"

        if week_label != current_week_label:
            week_num += 1
            current_week_label = week_label
            lines += ["", f"### Week {week_num} — {week_label}", ""]

        lines += [
            f"#### Post {row['post_number']}: {row['title']}",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **Publish Date** | {row.get('day_of_week', '')} {pub_date} |",
            f"| **Primary Keyword** | {row.get('primary_keyword', '')} |",
            f"| **Topic Cluster** | {row.get('topic_cluster', '')} |",
            f"| **Funnel Stage** | {row.get('funnel_stage', '')} |",
            f"| **Content Type** | {row.get('content_type', '')} |",
            f"| **Brief** | {row.get('brief', '')} |",
            "",
            "**Outline:**",
            "",
            str(row.get("outline", "")),
            "",
            "---",
            "",
        ]

    return "\n".join(lines)
