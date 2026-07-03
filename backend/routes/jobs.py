# routes/jobs.py — endpoints for job data
# GET /jobs/new       → unseen jobs for tray.py + local UI
# GET /jobs/all       → full job history
# POST /jobs/skip     → mark a job skipped
# POST /jobs/approve  → mark a job applied

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_new_jobs, get_all_jobs, update_job_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


class StatusUpdate(BaseModel):
    job_id: str


@router.get("/new")
def list_new_jobs():
    """Jobs with status = new, sorted by score — this is what tray.py polls"""
    jobs = get_new_jobs()
    return {"count": len(jobs), "jobs": jobs}


@router.get("/all")
def list_all_jobs():
    """Full job history — for the local jobs page if you want to see everything"""
    jobs = get_all_jobs()
    return {"count": len(jobs), "jobs": jobs}


@router.post("/skip")
def skip_job(data: StatusUpdate):
    """Mark a job as skipped — won't show in /new again"""
    success = update_job_status(data.job_id, "skipped")
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update job")
    return {"status": "skipped", "job_id": data.job_id}


@router.post("/approve")
def approve_job(data: StatusUpdate):
    """Mark a job as applied"""
    success = update_job_status(data.job_id, "applied")
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update job")
    return {"status": "applied", "job_id": data.job_id}