from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ─── JOB ─────────────────────────────────────────────────

class Job(BaseModel):
    id: Optional[str] = None
    company: str
    role: str
    stack: List[str] = []
    score: Optional[int] = None
    url: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "new"        # new / applied / skipped / emailed
    reason: Optional[str] = None  # why this score
    urgent: bool = False
    created_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    status: str                   # what to update it to


# ─── CONFIG ──────────────────────────────────────────────

class Config(BaseModel):
    skills: List[str]
    role_type: str                # internship-ppo / full-time etc
    seniority: str                # junior / mid / senior
    min_score: int = 7
    agent_interval_hours: int = 2
    quiet_hours_start: int = 22
    quiet_hours_end: int = 8
    notify_mode: str = "instant" # instant / batch


# ─── SEARCH ──────────────────────────────────────────────

class SearchResult(BaseModel):
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None


# ─── RECRUITER ───────────────────────────────────────────

class Recruiter(BaseModel):
    name: str
    title: Optional[str] = None
    company: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    reason: Optional[str] = None  # why agent picked them


# ─── EMAIL ───────────────────────────────────────────────

class EmailDraft(BaseModel):
    to: str                       # recruiter email
    recruiter_name: str
    subject: str
    body: str
    job_id: str                   # which job this is for


class EmailSendRequest(BaseModel):
    job_id: str
    to: str
    subject: str
    body: str


# ─── DM ──────────────────────────────────────────────────

class DMDraft(BaseModel):
    person_name: str
    person_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    message: str
    job_id: str


# ─── AGENT RUN RESULT ────────────────────────────────────

class AgentRunResult(BaseModel):
    jobs_found: int = 0
    jobs_saved: int = 0
    jobs_skipped: int = 0
    errors: List[str] = []
    duration_seconds: Optional[float] = None