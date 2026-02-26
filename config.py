from datetime import date

# ---------------------------------------------------------------------------
# Competitor blog index pages to scrape
# ---------------------------------------------------------------------------
COMPETITOR_BLOGS = [
    {"name": "ShipBob",             "url": "https://www.shipbob.com/blog/"},
    {"name": "ShipMonk",            "url": "https://www.shipmonk.com/blog/"},
    {"name": "Whiplash",            "url": "https://www.whiplash.com/blog/"},
    {"name": "Red Stag Fulfillment","url": "https://redstagfulfillment.com/blog/"},
    {"name": "ShipHero",            "url": "https://shiphero.com/blog/"},
    {"name": "Flexport",            "url": "https://www.flexport.com/blog/"},
]

# ---------------------------------------------------------------------------
# ShipDudes existing topic coverage
# Empty = treat every competitor topic as a gap (starting from scratch)
# ---------------------------------------------------------------------------
SHIPDUDES_EXISTING_TOPICS = []

# ---------------------------------------------------------------------------
# Scraper settings
# ---------------------------------------------------------------------------
SCRAPER_SETTINGS = {
    "max_posts_per_competitor": 20,
    "request_delay_seconds": 2,
    "request_timeout_seconds": 15,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# ---------------------------------------------------------------------------
# Content calendar settings
# ---------------------------------------------------------------------------
CALENDAR_SETTINGS = {
    "total_posts": 30,
    "posts_per_week": 3,   # Publishes Mon / Wed / Fri
    "start_date": None,    # None = start from today
}

# ---------------------------------------------------------------------------
# ShipDudes business context — injected into every AI prompt
# ---------------------------------------------------------------------------
SHIPDUDES_CONTEXT = """
Company: ShipDudes (shipdudes.com)
Industry: 3PL ecommerce fulfillment
Target customers: CPG operators and DTC brands
Services: Outsourced warehousing, pick and pack, order fulfillment
Content goal: Drive inbound organic traffic and get ShipDudes recognized
  by Google and AI tools (ChatGPT, Claude, Gemini) as a top 3PL provider
Tone: Authoritative, practical, founder-friendly — no corporate fluff
""".strip()

# ---------------------------------------------------------------------------
# AI model
# ---------------------------------------------------------------------------
AI_MODEL = "claude-sonnet-4-6"
