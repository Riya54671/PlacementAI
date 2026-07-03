# routes/recruiter.py — finds recruiters + drafts outreach
# POST /recruiter/find  → find recruiter for a job
# POST /recruiter/dm    → draft a LinkedIn DM

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from email_finder import find_recruiter_email
from email_drafter import draft_cold_email
from db import get_config
import json
import os
from groq import Groq
from prompts import DM_DRAFT_PROMPT
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/recruiter", tags=["recruiter"])
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class RecruiterRequest(BaseModel):
    job_id: str
    company: str
    role: str
    stack: list = []
    description: str = ""
    company_domain: Optional[str] = None


class EmailRequest(BaseModel):
    job_id: str
    company: str
    role: str
    stack: list = []
    description: str = ""
    recruiter_name: str
    candidate_name: str
    background: str


class DMRequest(BaseModel):
    job_id: str
    company: str
    role: str
    person_name: str
    person_title: str = ""
    candidate_name: str


# ─── FIND RECRUITER ───────────────────────────────────────

@router.post("/find")
def find_recruiter(data: RecruiterRequest):
    """
    Find a recruiter at the company and return their details
    called when you click 'Find recruiter' on a job card
    """
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not found")

    recruiter = find_recruiter_email(
        company=data.company,
        role=data.role,
        company_domain=data.company_domain
    )

    if not recruiter:
        raise HTTPException(
            status_code=404,
            detail=f"No recruiter found at {data.company}"
        )

    return {
        "recruiter": recruiter,
        "job_id": data.job_id
    }


# ─── DRAFT COLD EMAIL ─────────────────────────────────────

@router.post("/email/draft")
def draft_email(data: EmailRequest):
    """
    Draft a personalised cold email for a specific job + recruiter
    called after recruiter is found and you want to email them
    """
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not found")

    draft = draft_cold_email(
        candidate_name=data.candidate_name,
        skills=config.skills,
        background=data.background,
        recruiter_name=data.recruiter_name,
        company=data.company,
        role=data.role,
        stack=data.stack,
        description=data.description
    )

    if not draft:
        raise HTTPException(
            status_code=500,
            detail="Email drafting failed"
        )

    return {
        "subject": draft["subject"],
        "body": draft["body"],
        "job_id": data.job_id
    }


# ─── DRAFT LINKEDIN DM ────────────────────────────────────

@router.post("/dm/draft")
def draft_dm(data: DMRequest):
    """
    Draft a short LinkedIn DM to a recruiter or employee
    under 60 words, casual and direct
    """
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not found")

    try:
        prompt = DM_DRAFT_PROMPT.format(
            candidate_name=data.candidate_name,
            skills=", ".join(config.skills[:5]),  # top 5 skills only
            person_name=data.person_name,
            person_title=data.person_title,
            company=data.company,
            role=data.role
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()

        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            result = result[start:end]

        data_parsed = json.loads(result)
        message = data_parsed.get("message", "")

        return {
            "message": message,
            "job_id": data.job_id,
            "person_name": data.person_name,
            "person_title": data.person_title
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DM drafting failed: {e}"
        )