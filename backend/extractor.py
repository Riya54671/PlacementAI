# extractor.py — sends scraped text to Groq
# extracts structured job data + scores it
# this is the AI brain of the agent

import os
import json
from typing import Optional, List
from dotenv import load_dotenv
from groq import Groq
from models import Job
from prompts import EXTRACTION_PROMPT, SCORING_PROMPT
from db import get_config, job_exists

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─── EXTRACT JOBS FROM RAW TEXT ──────────────────────────

def extract_jobs(raw_text: str, source_url: str) -> List[dict]:
    """Send scraped page text to Groq, returns list of extracted job dicts"""
    try:
        text = raw_text[:4000]

        prompt = EXTRACTION_PROMPT.format(raw_text=text)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()

        # extract just the JSON part — find first { or [ and last } or ]
        start = min(
            (result.find("{") if "{" in result else len(result)),
            (result.find("[") if "[" in result else len(result))
        )
        end = max(result.rfind("}"), result.rfind("]")) + 1

        if start < end:
            result = result[start:end]

        try:
            data = json.loads(result)
        except json.JSONDecodeError as je:
            print(f"   ⚠️  Groq returned invalid JSON — skipping")
            print(f"   🔍 Raw output was: {result[:500]}")
            return []

        if isinstance(data, dict) and data.get("skip"):
            print(f"   ⏭️  Not a job listing — skipping")
            return []

        jobs = data if isinstance(data, list) else [data]

        for job in jobs:
            if not job.get("url"):
                job["url"] = source_url

        print(f"   📋 Extracted {len(jobs)} job(s)")
        return jobs

    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return []

# ─── SCORE A JOB ─────────────────────────────────────────

def score_job(job: dict, config) -> dict:
    """Score a job 1-10 based on your profile"""
    try:
        stack_value = job.get("stack", [])
        if not isinstance(stack_value, list):
            stack_value = []

        prompt = SCORING_PROMPT.format(
            skills=", ".join(config.skills),
            role_type=config.role_type,
            seniority=config.seniority,
            company=job.get("company", "Unknown"),
            role=job.get("role", "Unknown"),
            stack=", ".join(stack_value),
            description=job.get("description", "")
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()

        scored = json.loads(result)
        job["score"]  = scored.get("score", 0)
        job["reason"] = scored.get("reason", "")
        job["urgent"] = scored.get("urgent", False)

        print(f"   ⭐ Score: {job['score']}/10 — {job['reason']}")
        return job

    except Exception as e:
        print(f"   ❌ Scoring failed: {e}")
        job["score"]  = 0
        job["reason"] = "scoring failed"
        job["urgent"] = False
        return job
    
# ─── DUPLICATE CHECK ─────────────────────────────────────

def is_duplicate(job: dict) -> bool:
    """Check if this job already exists in DB"""
    if job_exists(job.get("company", ""), job.get("role", "")):
        print(f"   🔁 Duplicate found — skipping")
        return True
    return False


# ─── PROCESS A PAGE ──────────────────────────────────────

def process_page(raw_text: str, source_url: str, config) -> List[Job]:
    """Full pipeline: extract → deduplicate → score → return valid jobs"""
    raw_jobs = extract_jobs(raw_text, source_url)
    if not raw_jobs:
        return []

    valid_jobs = []

    for raw_job in raw_jobs:
        if not raw_job.get("company") or not raw_job.get("role"):
            print(f"   ⚠️  Missing company or role — skipping")
            continue

        if is_duplicate(raw_job):
            continue

        scored = score_job(raw_job, config)

        if scored["score"] < config.min_score:
            print(f"   📉 Score {scored['score']} below threshold {config.min_score} — skipping")
            continue

        stack_val = scored.get("stack") or []
        if not isinstance(stack_val, list):
            stack_val = []

        job = Job(
        company  = scored.get("company", "Unknown"),
        role     = scored.get("role", "Unknown"),
        stack    = stack_val,
        score    = scored.get("score", 0),
        url      = scored.get("url", source_url),
        deadline = scored.get("deadline"),
        reason   = scored.get("reason", ""),
        urgent   = scored.get("urgent", False),
        status   = "new"
        )

        valid_jobs.append(job)
        print(f"   ✅ Valid job: {job.company} — {job.role} ({job.score}/10)")

    return valid_jobs


# ─── TEST ────────────────────────────────────────────────

if __name__ == "__main__":
    from scrape import scrape

    print("Testing extractor.py...\n")

    config = get_config()
    if not config:
        print("❌ Could not load config")
        exit()

    test_url = "https://www.google.com/about/careers/applications/jobs/results"
    print(f"Scraping {test_url}...\n")

    raw_text = scrape(test_url)
    if not raw_text:
        print("❌ Scraping failed")
        exit()

    print(f"\nExtracting and scoring jobs...\n")
    jobs = process_page(raw_text, test_url, config)

    print(f"\n{'='*50}")
    print(f"Found {len(jobs)} valid job(s):\n")
    for job in jobs:
        print(f"  🏢 {job.company} — {job.role}")
        print(f"  ⭐ Score: {job.score}/10")
        print(f"  🛠️  Stack: {', '.join(job.stack)}")
        print(f"  📝 Reason: {job.reason}")
        print(f"  🔗 URL: {job.url}")
        print()