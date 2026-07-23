# search.py — finds job URLs using DuckDuckGo
# no API key needed for search, completely free
# uses Groq (free) for smart query generation

from ddgs import DDGS
from typing import List
import time
import json
import os
from dotenv import load_dotenv
from groq import Groq
from prompts import SEARCH_QUERY_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─── GENERATE SMART QUERIES ──────────────────────────────

def generate_queries(config) -> List[str]:
    previous = _load_previous_searches()
    
    try:
        prompt = SEARCH_QUERY_PROMPT.format(
            skills=", ".join(config.skills),
            role_type=config.role_type,
            seniority=config.seniority,
            previous_searches=", ".join(previous[-20:]) if previous else "none yet"
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. Always respond with ONLY valid JSON. No explanation, no markdown, no extra text before or after the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()

        # strip markdown fences
        text = text.replace("```json", "").replace("```", "").strip()

        # find the JSON object boundaries
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        # try parsing — if it fails, extract queries manually
        try:
            data = json.loads(text)
            queries = data.get("queries", [])
        except json.JSONDecodeError:
            # fallback — extract quoted strings that look like queries
            import re
            queries = re.findall(r'"([^"]{20,})"', text)
            queries = [q for q in queries if q != "queries"]
            print(f"   ⚠️  JSON parse failed, extracted {len(queries)} queries via regex")

        if not queries or len(queries) < 3:
            raise ValueError("Too few queries generated")

        _save_previous_searches(queries)
        print(f"🔍 Generated {len(queries)} search queries")
        return queries

    except Exception as e:
        print(f"❌ Query generation failed: {e}")
        return _fallback_queries()

def _load_previous_searches() -> list:
    """Load previous search queries from file"""
    try:
        if os.path.exists("previous_searches.json"):
            with open("previous_searches.json", "r") as f:
                return json.load(f)
    except:
        pass
    return []


def _save_previous_searches(queries: list):
    """Save search queries to avoid repeating next run"""
    try:
        existing = _load_previous_searches()
        all_searches = existing + queries
        # keep only last 50 to avoid prompt getting too long
        all_searches = all_searches[-50:]
        with open("previous_searches.json", "w") as f:
            json.dump(all_searches, f)
    except:
        pass


def _fallback_queries() -> list:
    """Hardcoded fallback if Groq fails"""
    return [
        "Groww software engineering internship PPO 2026",
        "CRED backend intern india apply",
        "PhonePe software intern ppo bangalore",
        "site:careers.meesho.com internship",
        "Zepto tech internship 2026 india",
        "wellfound.com react nodejs intern india",
        "cutshort.io python backend internship ppo",
        "BrowserStack software engineering intern apply",
    ]

# ─── SEARCH JOB URLS ─────────────────────────────────────

def search_jobs(queries: List[str]) -> List[str]:
    """Run each query, collect unique URLs"""
    urls = set()

    with DDGS() as ddgs:
        for query in queries:
            try:
                results = ddgs.text(query, max_results=8, timelimit='d')
                for r in results:
                    url = r.get("href", "")
                    if _is_useful_url(url):
                        urls.add(url)
                print(f"   ✅ '{query[:40]}...' → {len(results)} results")
                time.sleep(1) 
            except Exception as e:
                print(f"   ⚠️  Query failed: {e}")
                time.sleep(2)
                continue

    print(f"\n📋 Total unique URLs found: {len(urls)}")
    return list(urls)


# ─── SEARCH LINKEDIN PROFILES ────────────────────────────

def search_linkedin_profiles(company: str, role: str) -> List[dict]:
    """Find recruiters/employees at a company via DDG"""
    queries = [
        f'site:linkedin.com/in recruiter "{company}"',
        f'site:linkedin.com/in "talent acquisition" "{company}"',
        f'site:linkedin.com/in "engineering manager" "{company}"',
    ]

    people = []
    seen_urls = set()

    with DDGS() as ddgs:
        for query in queries:
            try:
                results = ddgs.text(query, max_results=5,timelimit='w')
                for r in results:
                    url = r.get("href", "")
                    if "linkedin.com/in/" in url and url not in seen_urls:
                        seen_urls.add(url)
                        print(f"   🔍 RAW title: {repr(r.get('title', ''))}")  # debug
                        people.append({
                            "name":         r.get("title", "Unknown").split(" - ")[0].split(" | ")[0].strip()[:50],
                            "title":        r.get("title", "")[:100],
                            "linkedin_url": url,
                            "snippet":      r.get("body", "")[:200],
                        })
                time.sleep(1)
            except Exception as e:
                print(f"⚠️  LinkedIn search failed: {e}")
                continue

    print(f"👥 Found {len(people)} people at {company}")
    return people


# ─── URL FILTER ──────────────────────────────────────────

def _is_useful_url(url: str) -> bool:
    """Strictly filter — only keep URLs that are likely actual job listings"""
    if not url:
        return False

    url_lower = url.lower()

    # hard skip — these are never job listings
    skip_domains = [
        "youtube.com", "facebook.com", "twitter.com", "x.com",
        "instagram.com", "reddit.com", "quora.com", "wikipedia.org",
        "medium.com", "substack.com", "hashnode.dev", "dev.to",
        "towardsdatascience.com", "analyticsvidhya.com",
        "geeksforgeeks.org", "leetcode.com", "hackerrank.com",
        "stackoverflow.com", "github.com", "gitlab.com",
        "bing.com", "google.com/aclk",
        "habr.com", "sysout.ru", "codeutility.io",
        "monikalearns.com", "placement-officer.com",
        "gethiredfaster.in", "thenewviews.com",
        "glassdoor.com", "ambitionbox.com",
        "timesjobs.com", "shine.com", "monster.com",
        "careerjet.co.in", "freshersworld.com",
        "placementseason.com", "campusplacements.com","piohindi.com", "internshipshub.in", "freshershunt.in",
        "vthetecheejobs.com", "thenewviews.com", "placementdrive.in",
        "jobformore.com", "internhq.com", "indiaai.gov.in",
        "consint.ai"
    ]
    for domain in skip_domains:
        if domain in url_lower:
            return False

    # skip URL patterns that are clearly not job listings
    skip_patterns = [
        "/blog/", "/article/", "/news/", "/press/",
        "/about/", "/locations/", "/team/", "/culture/",
        "/ru/", "/articles/", "/posts/", "/tutorials/",
        "/course/", "/learn/", "/guide/", "?q=", "?s=",
        "/tag/", "/category/", "/author/","/Interview/", "glassdoor.co.in"
    ]
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False

    # must have at least one job signal to be included
    job_signals = [
        "career", "job", "hiring", "intern", "recruit",
        "wellfound", "cutshort", "internshala", "naukri",
        "lever.co", "greenhouse.io", "workday.com",
        "instahyre", "linkedin.com/jobs", "linkedin.com/in",
        "apply", "opening", "vacancy", "position",
        "angellist", "workatastartup",
    ]
    for signal in job_signals:
        if signal in url_lower:
            return True

    # everything else — skip it
    return False

# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    from db import get_config

    print("Testing search.py...\n")
    config = get_config()

    if not config:
        print("❌ Could not load config")
        exit()

    print("1. Generating search queries...\n")
    queries = generate_queries(config)
    for i, q in enumerate(queries, 1):
        print(f"   {i}. {q}")

    print(f"\n2. Searching for jobs...\n")
    urls = search_jobs(queries[:3])
    print(f"\nSample URLs found:")
    for url in list(urls)[:5]:
        print(f"   → {url}")

    print(f"\n3. Searching LinkedIn for Stripe recruiters...\n")
    people = search_linkedin_profiles("Stripe", "software engineer")
    for p in people[:3]:
        print(f"   → {p['name']} | {p['linkedin_url']}")