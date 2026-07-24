# agent.py — the main agentic loop
# search → scrape → extract → score → save
# this is what runs every 2 hours automatically

import time
from datetime import datetime
from db import get_config, save_job
from search import generate_queries, search_jobs
from scrape import scrape
from extractor import process_page
from models import AgentRunResult
from company_careers import CAREER_PAGES

# skip URLs that are clearly not job listings even after search
def is_likely_job_url(url: str) -> bool:
    skip_words = [
        "article", "blog", "tutorial", "guide", "learn",
        "course", "news", "press", "about", "team",
        "habr", "medium", "substack", "dev.to"
    ]
    url_lower = url.lower()
    return not any(word in url_lower for word in skip_words)

def run_agent(max_pages: int = 15) -> AgentRunResult:
    """
    Full agent cycle:
    1. Load your config
    2. Generate smart search queries
    3. Search for job URLs
    4. Scrape each page
    5. Extract + score jobs
    6. Save valid jobs to Supabase
    """
    start_time = time.time()
    result = AgentRunResult()

    print(f"\n{'='*60}")
    print(f"🤖 AGENT RUN STARTED — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # step 1 — load config
    config = get_config()
    if not config:
        result.errors.append("Could not load config")
        print("❌ Could not load config — aborting run")
        return result

    print(f"👤 Profile: {config.role_type} | {config.seniority} | min score {config.min_score}")
    print(f"🛠️  Skills: {', '.join(config.skills)}\n")

    # step 2 — generate search queries
    print("STEP 1 — Generating search queries\n")
    queries = generate_queries(config)

    if not queries:
        result.errors.append("No search queries generated")
        print("❌ No queries generated — aborting run")
        return result

    # step 3 — search for URLs
    print(f"\nSTEP 2 — Searching for job URLs\n")
    urls = search_jobs(queries)
    all_urls = list(set(urls + CAREER_PAGES))
    print(f"\n📦 Total URLs (search + curated): {len(all_urls)}")

    if not urls:
        result.errors.append("No URLs found")
        print("❌ No URLs found — aborting run")
        return result

    # limit how many pages we process per run
    curated = [u for u in all_urls if u in CAREER_PAGES]
    searched = [u for u in all_urls if u not in CAREER_PAGES]
    urls = curated + searched
    urls = urls[:max_pages]
    print(f"\n📦 Processing {len(urls)} URLs this run\n")
    
    urls = [u for u in urls if is_likely_job_url(u)]
    print(f"\n📦 Processing {len(urls[:max_pages])} URLs this run\n")
    urls = urls[:max_pages]

    # step 4, 5, 6 — scrape, extract, score, save each URL
    print(f"STEP 3 — Scraping, extracting, scoring\n")

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url[:70]}")

        try:
            # scrape the page
            raw_text = scrape(url)
            if not raw_text:
                result.errors.append(f"Scrape failed: {url}")
                continue

            # extract + score jobs from this page
            jobs = process_page(raw_text, url, config)
            result.jobs_found += len(jobs)

           # save each valid job
            for job in jobs:
                job_id = save_job(job)
                if job_id:
                    result.jobs_saved += 1
                    try:
                        from sheets import write_job
                        write_job({
                            "company": job.company,
                            "role": job.role,
                            "score": job.score,
                            "stack": job.stack,
                            "url": job.url,
                            "urgent": job.urgent
                        })
                    except Exception as e:
                        print(f"   ⚠️  Sheets sync failed: {e}")
                else:
                    result.jobs_skipped += 1
        except Exception as e:
            error_msg = f"Error processing {url}: {e}"
            print(f"   ❌ {error_msg}")
            result.errors.append(error_msg)
            continue

        time.sleep(1)  # be polite between pages

    # summary
    duration = time.time() - start_time
    result.duration_seconds = round(duration, 1)

    print(f"\n{'='*60}")
    print(f"✅ AGENT RUN COMPLETE")
    print(f"{'='*60}")
    print(f"   URLs processed:  {len(urls)}")
    print(f"   Jobs found:      {result.jobs_found}")
    print(f"   Jobs saved:      {result.jobs_saved}")
    print(f"   Jobs skipped:    {result.jobs_skipped}")
    print(f"   Errors:          {len(result.errors)}")
    print(f"   Duration:        {result.duration_seconds}s")
    print(f"{'='*60}\n")

    return result


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    # run with a small max_pages for testing — don't burn through everything
    result = run_agent(max_pages=5)

    if result.jobs_saved > 0:
        print(f"🎉 Saved {result.jobs_saved} new job(s) to your database!")
        print(f"   Check your Supabase jobs table to see them.")
    else:
        print(f"😕 No jobs met your threshold this run.")
        print(f"   This is normal sometimes — try running again later")
        print(f"   or consider lowering min_score temporarily to test.")