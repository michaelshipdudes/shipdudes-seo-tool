"""
scraper.py
Fetches blog titles, meta descriptions, and H1-H3 headings
from each competitor's blog index page and individual posts.
"""

import time
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import COMPETITOR_BLOGS, SCRAPER_SETTINGS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers():
    return {
        "User-Agent": SCRAPER_SETTINGS["user_agent"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def _get(url):
    """GET with configured timeout and headers. Returns Response or None."""
    try:
        resp = requests.get(
            url,
            headers=_headers(),
            timeout=SCRAPER_SETTINGS["request_timeout_seconds"],
        )
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"    [SKIP] {url} — {e}")
        return None


# ---------------------------------------------------------------------------
# Step 1: Collect blog post URLs from an index page
# ---------------------------------------------------------------------------

def get_blog_post_links(blog_index_url, competitor_name):
    """
    Visit a blog index page and return a list of individual post URLs.
    Only returns links that are deeper than the index path itself.
    """
    max_posts = SCRAPER_SETTINGS["max_posts_per_competitor"]
    print(f"  Collecting post links from {blog_index_url} ...")

    resp = _get(blog_index_url)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    parsed_index = urlparse(blog_index_url)
    base_domain = parsed_index.netloc
    index_path = parsed_index.path.rstrip("/")

    # Patterns that indicate navigation / pagination rather than posts
    skip_patterns = ["/page/", "/tag/", "/category/", "/author/", "/feed/", "?"]

    found = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue

        full_url = urljoin(blog_index_url, href)
        p = urlparse(full_url)

        # Must be same domain
        if p.netloc != base_domain:
            continue

        # Path must start with the blog index path and be deeper
        path = p.path.rstrip("/")
        if not path.startswith(index_path + "/"):
            continue
        if len(path) <= len(index_path) + 1:
            continue

        # Skip non-post pages
        if any(pattern in full_url for pattern in skip_patterns):
            continue

        # Normalise (drop query string / fragment)
        clean = f"{p.scheme}://{p.netloc}{p.path}"
        found.add(clean)

    links = list(found)[:max_posts]
    print(f"  Found {len(links)} post links for {competitor_name}")
    return links


# ---------------------------------------------------------------------------
# Step 2: Scrape a single post page
# ---------------------------------------------------------------------------

def scrape_page(url):
    """
    Extract SEO fields from one blog post URL.
    Returns a dict or None if the page could not be fetched.
    """
    time.sleep(SCRAPER_SETTINGS["request_delay_seconds"])

    resp = _get(url)
    if resp is None:
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # --- Title tag ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # --- Meta description (name or og:description fallback) ---
    meta = soup.find("meta", attrs={"name": "description"}) or \
           soup.find("meta", attrs={"property": "og:description"})
    meta_description = (meta.get("content", "").strip() if meta else "")[:300]

    # --- H1 ---
    h1_tags = soup.find_all("h1")
    h1 = " | ".join(h.get_text(strip=True) for h in h1_tags if h.get_text(strip=True))

    # --- H2s ---
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]

    # --- H3s ---
    h3s = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    return {
        "url": url,
        "title": title[:200],
        "meta_description": meta_description,
        "h1": h1[:300],
        "h2s": " | ".join(h2s[:12]),
        "h3s": " | ".join(h3s[:15]),
        # Raw list kept for topic classifier — dropped before CSV save
        "_all_headings": h2s + h3s,
    }


# ---------------------------------------------------------------------------
# Step 3: Scrape all competitors
# ---------------------------------------------------------------------------

def scrape_competitor(competitor):
    """Scrape all posts for one competitor. Returns list of dicts."""
    name = competitor["name"]
    index_url = competitor["url"]

    print(f"\n[Scraping] {name}")
    post_links = get_blog_post_links(index_url, name)

    if not post_links:
        print(f"  No posts found for {name} — skipping.")
        return []

    results = []
    for i, post_url in enumerate(post_links, 1):
        print(f"  [{i}/{len(post_links)}] {post_url}")
        data = scrape_page(post_url)
        if data:
            data["competitor"] = name
            results.append(data)

    print(f"  Scraped {len(results)}/{len(post_links)} posts successfully")
    return results


def scrape_all_competitors():
    """
    Scrape every competitor in COMPETITOR_BLOGS.
    Returns a DataFrame; empty if nothing was scraped.
    """
    all_results = []

    for competitor in COMPETITOR_BLOGS:
        posts = scrape_competitor(competitor)
        all_results.extend(posts)

    if not all_results:
        print("\n[WARNING] No data scraped from any competitor.")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    print(
        f"\n[Scraper Complete] {len(df)} posts scraped "
        f"from {df['competitor'].nunique()} competitors"
    )
    return df
