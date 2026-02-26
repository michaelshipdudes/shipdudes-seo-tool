"""
analyzer.py
Classifies each scraped post into topic clusters, then identifies
which clusters ShipDudes has zero coverage in (i.e., all of them to start).
"""

import re
import pandas as pd
from config import SHIPDUDES_EXISTING_TOPICS


# ---------------------------------------------------------------------------
# Topic cluster definitions
# Each key is a human-readable cluster name.
# Values are keyword phrases — if ANY phrase appears in a post's
# combined title + headings, the post is tagged to that cluster.
# ---------------------------------------------------------------------------

TOPIC_CLUSTERS = {
    "Order Fulfillment": [
        "order fulfillment", "ecommerce fulfillment", "fulfillment center",
        "fulfillment services", "fulfillment process", "fulfillment strategy",
        "order management", "order processing", "outsource fulfillment",
        "fulfillment solution",
    ],
    "Shipping & Carriers": [
        "shipping rates", "shipping costs", "shipping speed", "shipping carrier",
        "fedex", "ups", "usps", "dhl", "last mile", "freight",
        "two-day shipping", "same-day shipping", "shipping label",
        "shipping carrier", "carrier rates",
    ],
    "Warehousing": [
        "warehouse", "warehousing", "inventory storage", "warehouse management",
        "wms", "distribution center", "fulfillment warehouse", "storage fees",
    ],
    "Inventory Management": [
        "inventory management", "inventory tracking", "inventory levels",
        "stockout", "overstock", "safety stock", "reorder point", "sku",
        "inventory forecasting", "inventory optimization",
    ],
    "Returns Management": [
        "returns", "reverse logistics", "returns management",
        "return policy", "return rate", "restocking", "return portal",
    ],
    "DTC & Ecommerce": [
        "dtc", "direct to consumer", "direct-to-consumer", "d2c",
        "shopify", "woocommerce", "bigcommerce", "online store",
        "ecommerce brand", "ecommerce store", "ecommerce business",
    ],
    "CPG & Brand Strategy": [
        "cpg", "consumer packaged goods", "cpg brand",
        "product launch", "subscription box", "subscription fulfillment",
        "retail fulfillment", "omnichannel", "brand fulfillment",
    ],
    "3PL Selection & Comparison": [
        "how to choose", "choosing a 3pl", "3pl comparison",
        "3pl vs", "fulfillment partner", "logistics partner",
        "outsource", "in-house vs", "what is 3pl", "3pl provider",
        "best 3pl", "top 3pl",
    ],
    "Pricing & Cost": [
        "fulfillment cost", "fulfillment pricing", "how much does",
        "price", "rate card", "per order fee", "storage fee",
        "fulfillment fees", "cost of fulfillment",
    ],
    "Technology & Integrations": [
        "software integration", "api integration", "automation",
        "erp", "wms software", "oms", "shopify integration",
        "tech stack", "fulfillment software", "inventory software",
    ],
    "Scaling & Growth": [
        "scale your", "scaling", "grow your business", "expand operations",
        "peak season", "black friday", "q4 fulfillment", "holiday season",
        "hypergrowth", "scale fulfillment",
    ],
    "Pick & Pack / Kitting": [
        "pick and pack", "pick pack", "custom packaging", "kitting",
        "unboxing", "packing materials", "product assembly",
        "bundling", "kit assembly",
    ],
    "International Fulfillment": [
        "international shipping", "global fulfillment", "cross-border",
        "customs", "duties", "import", "export", "international fulfillment",
    ],
    "Customer Experience": [
        "customer experience", "customer satisfaction", "post-purchase",
        "shipping experience", "brand experience", "unboxing experience",
        "delivery experience",
    ],
    "Analytics & Reporting": [
        "analytics", "fulfillment reporting", "fulfillment metrics",
        "kpi", "dashboard", "real-time tracking", "order visibility",
        "fulfillment data",
    ],
    "Amazon & Marketplace": [
        "amazon fba", "amazon fulfillment", "amazon seller", "fba",
        "marketplace fulfillment", "multi-channel fulfillment", "mcf",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text):
    """Lowercase and strip punctuation for matching."""
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_post(row):
    """
    Return a list of matching cluster names for a single DataFrame row.
    Looks at title, h1, h2s, and meta_description combined.
    """
    combined = _clean(" ".join([
        str(row.get("title", "")),
        str(row.get("h1", "")),
        str(row.get("h2s", "")),
        str(row.get("meta_description", "")),
    ]))

    matched = []
    for cluster, keywords in TOPIC_CLUSTERS.items():
        if any(kw in combined for kw in keywords):
            matched.append(cluster)

    return matched if matched else ["General / Other"]


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def find_content_gaps(df):
    """
    For each topic cluster, count how many competitors have posts on it
    and collect example post titles.

    Returns a DataFrame ranked by priority_score (competitor breadth × depth).
    """
    if df.empty:
        print("[WARNING] No competitor data to analyse.")
        return pd.DataFrame()

    print("\n[Analysing] Classifying posts into topic clusters ...")

    # {cluster: {"competitors": set, "examples": [], "post_count": int}}
    coverage = {}

    for _, row in df.iterrows():
        competitor = row.get("competitor", "Unknown")
        clusters = classify_post(row)
        title = str(row.get("title", ""))[:80]

        for cluster in clusters:
            if cluster not in coverage:
                coverage[cluster] = {"competitors": set(), "examples": [], "post_count": 0}
            coverage[cluster]["competitors"].add(competitor)
            coverage[cluster]["post_count"] += 1
            if len(coverage[cluster]["examples"]) < 3:
                coverage[cluster]["examples"].append(f"{competitor}: {title}")

    # Filter out topics ShipDudes already covers
    existing_lower = {t.lower() for t in SHIPDUDES_EXISTING_TOPICS}

    rows = []
    for cluster, data in coverage.items():
        if cluster.lower() in existing_lower:
            continue
        rows.append({
            "topic": cluster,
            "competitor_count": len(data["competitors"]),
            "post_count": data["post_count"],
            "competitors_covering": ", ".join(sorted(data["competitors"])),
            "example_posts": " || ".join(data["examples"]),
            # More competitors covering it = higher priority
            "priority_score": len(data["competitors"]) * 10 + data["post_count"],
        })

    if not rows:
        print("[WARNING] No content gaps found.")
        return pd.DataFrame()

    gaps_df = (
        pd.DataFrame(rows)
        .sort_values("priority_score", ascending=False)
        .reset_index(drop=True)
    )

    print(f"[Analysis Complete] {len(gaps_df)} topic clusters identified\n")
    print("Top 10 opportunities by competitor coverage:")
    for _, r in gaps_df.head(10).iterrows():
        print(f"  {r['topic']:35s}  {r['competitor_count']} competitors / {r['post_count']} posts")

    return gaps_df


def get_raw_titles_for_ai(df, limit=60):
    """Return a deduplicated list of competitor post titles for AI prompts."""
    if df.empty:
        return []
    return df["title"].dropna().unique().tolist()[:limit]
