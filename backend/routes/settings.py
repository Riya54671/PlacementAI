# routes/settings.py — read and update your config
# GET /settings → current settings
# PUT /settings → update one or more fields

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from db import get_config, update_config

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    skills: Optional[List[str]] = None
    role_type: Optional[str] = None
    seniority: Optional[str] = None
    min_score: Optional[int] = None
    agent_interval_hours: Optional[int] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    notify_mode: Optional[str] = None


@router.get("")
def get_settings():
    """Get your current config"""
    config = get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.put("")
def update_settings(data: SettingsUpdate):
    """Update one or more settings — only sends fields you actually changed"""
    updates = {k: v for k, v in data.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    success = update_config(updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update settings")

    return {"status": "updated", "fields": list(updates.keys())}