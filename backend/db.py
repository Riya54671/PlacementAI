# db.py — all Supabase operations in one place

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from models import Job, Config
from typing import List, Optional

load_dotenv()


# ─── CLIENT ──────────────────────────────────────────────

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# ─── CONFIG ──────────────────────────────────────────────

def get_config() -> Optional[Config]:
    """Read your settings from Supabase config table"""
    try:
        res = supabase.table("config").select("*").eq("id", 1).single().execute()
        return Config(**res.data)
    except Exception as e:
        print(f" Error fetching config: {e}")
        return None


def update_config(updates: dict) -> bool:
    """Update one or more config fields"""
    try:
        supabase.table("config").update(updates).eq("id", 1).execute()
        return True
    except Exception as e:
        print(f" Error updating config: {e}")
        return False


# ─── JOBS ────────────────────────────────────────────────

def save_job(job: Job) -> Optional[str]:
    """Save a new job, return its id"""
    try:
        data = {
            "company":  job.company,
            "role":     job.role,
            "stack":    job.stack,
            "score":    job.score,
            "url":      job.url,
            "deadline": job.deadline,
            "status":   job.status,
            "reason":   job.reason,
            "urgent":   job.urgent,
        }
        res = supabase.table("jobs").insert(data).execute()
        job_id = res.data[0]["id"]
        print(f" Saved: {job.company} — {job.role} (score {job.score})")
        return job_id
    except Exception as e:
        print(f" Error saving job: {e}")
        return None


def get_new_jobs() -> List[dict]:
    """Get all jobs with status = new"""
    try:
        res = (
            supabase.table("jobs")
            .select("*")
            .eq("status", "new")
            .order("score", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f" Error fetching new jobs: {e}")
        return []


def get_all_jobs() -> List[dict]:
    """Get all jobs ordered by created date"""
    try:
        res = (
            supabase.table("jobs")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f" Error fetching all jobs: {e}")
        return []


def update_job_status(job_id: str, status: str) -> bool:
    """Update job status — new/applied/skipped/emailed"""
    try:
        supabase.table("jobs").update({"status": status}).eq("id", job_id).execute()
        print(f" Job {job_id} → {status}")
        return True
    except Exception as e:
        print(f" Error updating job: {e}")
        return False


def job_exists(company: str, role: str) -> bool:
    """Check if we already have this job — prevents duplicates"""
    try:
        res = (
            supabase.table("jobs")
            .select("id")
            .ilike("company", f"%{company}%")
            .ilike("role", f"%{role}%")
            .execute()
        )
        return len(res.data) > 0
    except Exception as e:
        print(f" Error checking duplicate: {e}")
        return False


def get_recent_job_titles() -> List[str]:
    """Get recent company+role combos for duplicate checking"""
    try:
        res = (
            supabase.table("jobs")
            .select("company, role")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return [f"{j['company']} — {j['role']}" for j in res.data]
    except Exception as e:
        print(f" Error fetching recent jobs: {e}")
        return []


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing Supabase connection...\n")

    config = get_config()
    if config:
        print(f" Config loaded!")
        print(f"   Skills:    {config.skills}")
        print(f"   Role type: {config.role_type}")
        print(f"   Min score: {config.min_score}")
    else:
        print(" Could not load config — check your .env keys")