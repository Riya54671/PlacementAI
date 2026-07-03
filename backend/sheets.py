# sheets.py — syncs job activity to Google Sheets
# every action you take gets logged automatically
# you never manually enter anything

import os
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = "sheets_token.json"
CREDS_FILE = "gmail_credentials.json"  # reuse same credentials file


# ─── AUTHENTICATE ─────────────────────────────────────────

def get_sheets_service():
    """Get authenticated Sheets service — same OAuth flow as Gmail"""
    if not SHEETS_AVAILABLE:
        print("⚠️  Sheets API not installed")
        return None

    if not SHEETS_ID:
        print("⚠️  GOOGLE_SHEETS_ID not set in .env — skipping sheets sync")
        return None

    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                print(f"⚠️  {CREDS_FILE} not found — skipping sheets sync")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


# ─── SETUP HEADERS ────────────────────────────────────────

def setup_sheet_headers():
    """
    Add column headers to your sheet on first use
    run this once manually to set up the sheet
    """
    service = get_sheets_service()
    if not service:
        return False

    headers = [[
        "Company",
        "Role",
        "Score",
        "Stack",
        "URL",
        "Status",
        "Email Sent To",
        "LinkedIn URL",
        "Urgent",
        "Found On",
        "Last Updated"
    ]]

    try:
        service.spreadsheets().values().update(
            spreadsheetId=SHEETS_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": headers}
        ).execute()
        print("✅ Sheet headers set up")
        return True
    except Exception as e:
        print(f"❌ Failed to set up headers: {e}")
        return False


# ─── WRITE JOB ROW ────────────────────────────────────────

def write_job(job: dict) -> bool:
    """
    Add a new row when agent finds a job
    called automatically in agent.py after save_job()
    """
    service = get_sheets_service()
    if not service:
        return False

    try:
        row = [[
            job.get("company", ""),
            job.get("role", ""),
            job.get("score", ""),
            ", ".join(job.get("stack", [])) if isinstance(job.get("stack"), list) else "",
            job.get("url", ""),
            "New",
            "",  # email sent to — filled later
            "",  # linkedin url — filled later
            "Yes" if job.get("urgent") else "No",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ]]

        service.spreadsheets().values().append(
            spreadsheetId=SHEETS_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": row}
        ).execute()

        print(f"📊 Sheet updated: {job.get('company')} — {job.get('role')}")
        return True

    except Exception as e:
        print(f"❌ Sheets write failed: {e}")
        return False


# ─── UPDATE STATUS ────────────────────────────────────────

def update_status(company: str, role: str, status: str,
                  email_sent_to: str = None,
                  linkedin_url: str = None) -> bool:
    """
    Update a row's status when you act on a job
    matches by company + role since we don't store row numbers
    """
    service = get_sheets_service()
    if not service:
        return False

    try:
        # read all rows to find the right one
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEETS_ID,
            range="Sheet1!A:K"
        ).execute()

        rows = result.get("values", [])

        for i, row in enumerate(rows):
            if len(row) >= 2:
                if row[0].lower() == company.lower() and \
                   row[1].lower() == role.lower():
                    # found the row — update it
                    row_num = i + 1  # sheets is 1-indexed
                    updates = []

                    # update status (column F = index 6)
                    updates.append({
                        "range": f"Sheet1!F{row_num}",
                        "values": [[status]]
                    })

                    # update email if provided (column G = index 7)
                    if email_sent_to:
                        updates.append({
                            "range": f"Sheet1!G{row_num}",
                            "values": [[email_sent_to]]
                        })

                    # update linkedin if provided (column H = index 8)
                    if linkedin_url:
                        updates.append({
                            "range": f"Sheet1!H{row_num}",
                            "values": [[linkedin_url]]
                        })

                    # update last updated (column K = index 11)
                    updates.append({
                        "range": f"Sheet1!K{row_num}",
                        "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]
                    })

                    service.spreadsheets().values().batchUpdate(
                        spreadsheetId=SHEETS_ID,
                        body={"valueInputOption": "RAW", "data": updates}
                    ).execute()

                    print(f"📊 Sheet status updated: {company} → {status}")
                    return True

        print(f"⚠️  Row not found in sheet: {company} — {role}")
        return False

    except Exception as e:
        print(f"❌ Sheets update failed: {e}")
        return False


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing sheets.py...\n")

    if not SHEETS_ID:
        print("❌ GOOGLE_SHEETS_ID not set in .env")
        print("   Create a Google Sheet, copy the ID from the URL")
        print("   URL looks like: docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit")
        exit()

    print("Setting up headers...")
    setup_sheet_headers()

    print("\nWriting test job row...")
    write_job({
        "company": "Razorpay",
        "role": "Full Stack Development Intern",
        "score": 9,
        "stack": ["React", "Node.js", "PostgreSQL"],
        "url": "https://razorpay.com/jobs/",
        "urgent": False
    })

    print("\nUpdating status...")
    update_status("Razorpay", "Full Stack Development Intern", "Applied")

    print("\n✅ Check your Google Sheet — should show the test row!")