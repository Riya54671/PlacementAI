# scraper.py — reads content from career pages
# tries Jina Reader first (fast, free, no install)
# falls back to Crawl4AI for JS-heavy pages
# last resort: basic requests

import requests
import asyncio
from typing import Optional
import time

# ─── JINA READER (primary) ───────────────────────────────

def scrape_with_jina(url: str) -> Optional[str]:
    """
    Jina Reader converts any URL to clean text
    completely free, no API key, no install needed
    just prepend https://r.jina.ai/ to any URL
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {"Accept": "text/plain"}
        response = requests.get(jina_url, headers=headers, timeout=15)

        if response.status_code == 200:
            text = response.text.strip()
            if len(text) > 200:  # ignore empty/tiny pages
                print(f"   ✅ Jina scraped: {url[:50]}...")
                return text
        return None
    except Exception as e:
        print(f"   ⚠️  Jina failed: {e}")
        return None


# ─── CRAWL4AI (fallback for JS pages) ───────────────────

async def scrape_with_crawl4ai(url: str) -> Optional[str]:
    """
    Crawl4AI handles JavaScript-heavy pages
    free, open source, runs locally
    """
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            if result.success and result.markdown:
                text = result.markdown.strip()
                if len(text) > 200:
                    print(f"   ✅ Crawl4AI scraped: {url[:50]}...")
                    return text
        return None
    except Exception as e:
        print(f"   ⚠️  Crawl4AI failed: {e}")
        return None


# ─── BASIC REQUESTS (last resort) ────────────────────────

def scrape_with_requests(url: str) -> Optional[str]:
    """Simple requests fallback — works on non-JS pages"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # very basic — just get raw text
            text = response.text[:5000]  # limit size
            if len(text) > 200:
                print(f"   ✅ Requests scraped: {url[:50]}...")
                return text
        return None
    except Exception as e:
        print(f"   ⚠️  Requests failed: {e}")
        return None


# ─── MAIN SCRAPER ─────────────────────────────────────────

def scrape(url: str) -> Optional[str]:
    """
    Try each scraper in order, return first success
    Jina → Crawl4AI → basic requests
    """
    print(f"\n🔎 Scraping: {url[:60]}...")

    # 1. try Jina first — fastest and cleanest
    text = scrape_with_jina(url)
    if text:
        return text

    # 2. try Crawl4AI for JS-heavy pages
    text = asyncio.run(scrape_with_crawl4ai(url))
    if text:
        return text

    # 3. last resort — basic requests
    text = scrape_with_requests(url)
    if text:
        return text

    print(f"   ❌ All scrapers failed for: {url[:50]}")
    return None


def scrape_multiple(urls: list, max_pages: int = 20) -> dict:
    """
    Scrape multiple URLs, return dict of url → text
    limits to max_pages to avoid running forever
    """
    results = {}
    urls = urls[:max_pages]  # cap it

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", end="")
        text = scrape(url)
        if text:
            results[url] = text
        time.sleep(1)  # be polite between requests

    print(f"\n\n📄 Successfully scraped {len(results)}/{len(urls)} pages")
    return results


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing scraper.py...\n")

    test_urls = [
        "https://stripe.com/jobs",
        "https://razorpay.com/jobs/",
        "https://www.google.com/about/careers/applications/",
    ]

    for url in test_urls:
        text = scrape(url)
        if text:
            print(f"\n--- Preview ({len(text)} chars) ---")
            print(text[:300])
            print("...")
        print("-" * 50)