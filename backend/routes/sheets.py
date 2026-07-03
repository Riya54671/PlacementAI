from fastapi import APIRouter
from pydantic import BaseModel
from sheets import update_status

router = APIRouter(prefix="/sheets", tags=["sheets"])

class SheetUpdate(BaseModel):
    company: str
    role: str
    status: str
    email_sent_to: str = ""
    linkedin_url: str = ""

@router.post("/update")
def sheets_update(data: SheetUpdate):
    update_status(
        company=data.company,
        role=data.role,
        status=data.status,
        email_sent_to=data.email_sent_to or None,
        linkedin_url=data.linkedin_url or None
    )
    return {"status": "ok"}