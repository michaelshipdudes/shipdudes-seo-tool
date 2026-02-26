"""
utils.py
Shared helpers used by every Streamlit page:
  - settings.json persistence
  - Anthropic API key injection
  - Output file helpers
  - Rule-based opportunity labels
  - Sidebar branding renderer
  - Global CSS
"""

import json
import os
import streamlit as st
from config import COMPETITOR_BLOGS

SETTINGS_FILE = "settings.json"
OUTPUT_DIR    = "output"

# ---------------------------------------------------------------------------
# Rule-based labels for the Opportunities page
# Derived from topic cluster names — no extra API calls needed.
# ---------------------------------------------------------------------------

CPG_DTC_RELEVANCE = {
    "DTC & Ecommerce":            "High",
    "CPG & Brand Strategy":       "High",
    "3PL Selection & Comparison": "High",
    "Order Fulfillment":          "High",
    "Returns Management":         "High",
    "Pick & Pack / Kitting":      "High",
    "Pricing & Cost":             "High",
    "Scaling & Growth":           "High",
    "Customer Experience":        "High",
    "Warehousing":                "Medium",
    "Inventory Management":       "Medium",
    "Shipping & Carriers":        "Medium",
    "Technology & Integrations":  "Medium",
    "International Fulfillment":  "Medium",
    "Analytics & Reporting":      "Medium",
    "Amazon & Marketplace":       "Low",
    "General / Other":            "Low",
}

# Topics that AI tools (ChatGPT, Claude, Gemini) commonly cite sources for
# when answering ecommerce operator questions.
AI_VISIBILITY = {
    "3PL Selection & Comparison": "High",
    "Order Fulfillment":          "High",
    "Pricing & Cost":             "High",
    "Pick & Pack / Kitting":      "High",
    "DTC & Ecommerce":            "High",
    "Warehousing":                "Medium",
    "Inventory Management":       "Medium",
    "Returns Management":         "Medium",
    "Shipping & Carriers":        "Medium",
    "Scaling & Growth":           "Medium",
    "CPG & Brand Strategy":       "Medium",
    "Technology & Integrations":  "Low",
    "International Fulfillment":  "Low",
    "Analytics & Reporting":      "Low",
    "Amazon & Marketplace":       "Low",
    "Customer Experience":        "Low",
    "General / Other":            "Low",
}


# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    default = {
        "competitors": COMPETITOR_BLOGS,
        "last_run": None,
        "last_run_stats": {},
    }
    save_settings(default)
    return default


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def inject_api_key():
    """Pull Anthropic key from st.secrets and expose as ANTHROPIC_API_KEY env var."""
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass  # Falls back to .env loaded by python-dotenv


# ---------------------------------------------------------------------------
# Output file helpers
# ---------------------------------------------------------------------------

def output_path(filename):
    return os.path.join(OUTPUT_DIR, filename)


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def output_exists(filename):
    return os.path.exists(output_path(filename))


# ---------------------------------------------------------------------------
# Data enrichment
# ---------------------------------------------------------------------------

def enrich_gaps_df(df):
    """Add CPG/DTC Relevance and AI Visibility columns (rule-based)."""
    df = df.copy()
    df["CPG/DTC Relevance"] = df["topic"].map(CPG_DTC_RELEVANCE).fillna("Medium")
    df["AI Visibility"]     = df["topic"].map(AI_VISIBILITY).fillna("Medium")
    return df


# ---------------------------------------------------------------------------
# Global CSS (injected on every page)
# ---------------------------------------------------------------------------

def get_global_css():
    return """
<style>
/* Tighten top padding */
.block-container { padding-top: 1.5rem !important; }

/* Metric cards */
div[data-testid="metric-container"] {
    background-color: #1B2D45;
    border: 1px solid #2A3F5F;
    border-radius: 12px;
    padding: 1rem 1.5rem;
}

/* Sidebar top padding */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}

/* Dataframe header row */
div[data-testid="stDataFrame"] thead tr th {
    background-color: #1B2D45 !important;
}

/* Links */
a { color: #FF6B35 !important; }

/* Success / info / error banners — subtly rounded */
div[data-testid="stAlert"] { border-radius: 10px; }
</style>
"""


# ---------------------------------------------------------------------------
# Sidebar branding (call from every page after set_page_config)
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown("""
<div style="padding:0.25rem 0 1.25rem 0;">
  <div style="font-size:1.85rem;font-weight:900;color:#FF6B35;
              letter-spacing:-1px;line-height:1.1;">ShipDudes</div>
  <div style="font-size:0.68rem;color:#8BA3BF;letter-spacing:0.08em;
              text-transform:uppercase;margin-top:3px;">
      SEO Content Intelligence Tool
  </div>
</div>
""", unsafe_allow_html=True)

        settings = load_settings()
        last_run = settings.get("last_run")
        if last_run:
            st.caption(f"Last run: {last_run}")
        else:
            st.caption("No analysis run yet")
        st.divider()
