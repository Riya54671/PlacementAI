# routes/email.py — send cold emails via Gmail
# POST /email/send  → sends a drafted email
# POST /email/preview → returns preview without sending

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from email_sender import send_email, preview_email
from sheets import update_status
from db import update_job_status

router = APIRouter(prefix="/email", tags=["email"])


class SendEmailRequest(BaseModel):
    job_id: str
    company: str
    role: str
    to: str
    subject: str
    body: str
    recruiter_linkedin: str = ""


class PreviewRequest(BaseModel):
    to: str
    subject: str
    body: str


# ─── SEND EMAIL ───────────────────────────────────────────

@router.post("/send")
def send_cold_email(data: SendEmailRequest):
    """
    Send a cold email — only called after you review and approve
    updates job status to emailed + syncs to Google Sheets
    """
    success = send_email(
        to=data.to,
        subject=data.subject,
        body=data.body,
        job_id=data.job_id
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Email sending failed — check Gmail credentials"
        )

    # update job status to emailed
    update_job_status(data.job_id, "emailed")

    # sync to Google Sheets
    update_status(
        company=data.company,
        role=data.role,
        status="Email sent",
        email_sent_to=data.to,
        linkedin_url=data.recruiter_linkedin
    )

    return {
        "status": "sent",
        "to": data.to,
        "job_id": data.job_id
    }


# ─── PREVIEW EMAIL ────────────────────────────────────────

@router.post("/preview")
def preview_cold_email(data: PreviewRequest):
    """
    Return email preview — shown in UI before you confirm send
    doesn't actually send anything
    """
    return {
        "to": data.to,
        "subject": data.subject,
        "body": data.body,
        "preview": True
    }