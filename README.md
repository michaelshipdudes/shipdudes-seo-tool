# ShipDudes SEO Content Tool

Scrapes competitor 3PL blogs, identifies content gaps, and generates a
30-day content calendar with AI-written outlines using Claude.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add your Anthropic API key
```bash
cp .env.example .env
# Open .env and paste your key
```

### 3. Run the tool
```bash
python main.py
```

Runtime is roughly **5–10 minutes** (scraping + 30 outline API calls).

---

## Output files

| File | Contents |
|------|----------|
| `output/competitor_data.csv` | Raw scraped data — title, meta description, H1-H3 headings per post |
| `output/content_gaps.csv` | Topic clusters competitors cover, ranked by opportunity score |
| `output/content_calendar.csv` | 30-day schedule — title, keyword, funnel stage, publish date |
| `output/content_plan.md` | Full report — calendar + detailed outline for every post |

---

## Customisation

| What to change | Where |
|----------------|-------|
| Add/remove competitors | `config.py` → `COMPETITOR_BLOGS` |
| Mark topics as already covered | `config.py` → `SHIPDUDES_EXISTING_TOPICS` |
| Posts per week / start date | `config.py` → `CALENDAR_SETTINGS` |
| Max posts scraped per competitor | `config.py` → `SCRAPER_SETTINGS["max_posts_per_competitor"]` |
| AI model | `config.py` → `AI_MODEL` |

---

## Project structure

```
shipdudes-seo-tool/
├── main.py                  # Entry point
├── config.py                # All settings and competitor URLs
├── scraper.py               # BeautifulSoup competitor blog scraper
├── analyzer.py              # Topic cluster gap analysis
├── calendar_generator.py    # Anthropic API — calendar + outlines
├── output/                  # Generated files land here
├── requirements.txt
├── .env.example
└── README.md
```
