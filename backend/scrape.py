# scraper.py — two scrapers only
# Jina Reader (primary) + BeautifulSoup (fallback)
# both free, no API keys needed

import requests
import os
from typing import Optional
from bs4 import BeautifulSoup


# ─── JINA READER (primary) ───────────────────────────────

def scrape_with_jina(url: str) -> Optional[str]:
    """
    Jina Reader converts any URL to clean markdown
    free, no API key, no install needed
    just prepend https://r.jina.ai/ to any URL
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {"Accept": "text/plain"}
        response = requests.get(jina_url, headers=headers, timeout=15)

        if response.status_code == 200:
            text = response.text.strip()
            if len(text) > 200:
                print(f"   ✅ Jina scraped: {url[:50]}...")
                return text[:8000]
        return None
    except Exception as e:
        print(f"   ⚠️  Jina failed: {e}")
        return None


# ─── BEAUTIFULSOUP (fallback) ─────────────────────────────

def scrape_with_bs4(url: str) -> Optional[str]:
    """
    Requests + BeautifulSoup fallback
    strips all junk tags, returns clean readable text
    works on any page that doesn't require JavaScript
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # remove all junk tags
        for tag in soup(["script", "style", "nav", "footer",
                          "header", "iframe", "noscript",
                          "meta", "link", "svg", "img"]):
            tag.decompose()

        # get clean text
        text = soup.get_text(separator="\n", strip=True)

        # collapse multiple blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        text = "\n".join(lines)[:8000]

        if len(text) > 200:
            print(f"   ✅ BS4 scraped: {url[:50]}...")
            return text

        return None
    except Exception as e:
        print(f"   ⚠️  BS4 failed: {e}")
        return None


# ─── MAIN SCRAPER ─────────────────────────────────────────

def scrape(url: str) -> Optional[str]:
    """
    Try Jina first, fall back to BeautifulSoup
    simple, reliable, completely free
    """
    print(f"\n🔎 Scraping: {url[:60]}...")

    # 1. Jina — best quality
    text = scrape_with_jina(url)
    if text:
        return text

    # 2. BS4 — always works as fallback
    text = scrape_with_bs4(url)
    if text:
        return text

    print(f"   ❌ All scrapers failed for: {url[:50]}")
    return None


def scrape_multiple(urls: list, max_pages: int = 20) -> dict:
    """Scrape multiple URLs, return dict of url → text"""
    import time
    results = {}
    urls = urls[:max_pages]

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", end="")
        text = scrape(url)
        if text:
            results[url] = text
        time.sleep(1)

    print(f"\n\n📄 Successfully scraped {len(results)}/{len(urls)} pages")
    return results


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing scraper.py...\n")

    test_urls = [
        "https://internshala.com/internships/node-js-development-internship/",
        "https://wellfound.com/jobs/3047433-sde-intern",
        "https://razorpay.com/jobs/",
    ]

    for url in test_urls:
        text = scrape(url)
        if text:
            print(f"\n--- Preview ({len(text)} chars) ---")
            print(text[:300])
            print("...")
        print("-" * 50)