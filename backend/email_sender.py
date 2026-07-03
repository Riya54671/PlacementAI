# email_sender.py — sends cold emails via Gmail API
# uses OAuth2 — you stay in full control of your Gmail
# emails come from YOUR actual Gmail address

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("⚠️  Gmail API not installed — run: pip install google-auth google-auth-oauthlib google-api-python-client")

# Gmail scope — only send permission, not read
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "gmail_token.json"
CREDS_FILE = "gmail_credentials.json"


# ─── AUTHENTICATE ─────────────────────────────────────────

def get_gmail_service():
    """
    Get authenticated Gmail service
    first run opens browser for OAuth consent
    after that uses saved token automatically
    """
    if not GMAIL_AVAILABLE:
        return None

    creds = None

    # load saved token if exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # if no valid token, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                print(f"❌ Gmail credentials file not found: {CREDS_FILE}")
                print(f"   Download it from Google Cloud Console → APIs → Credentials")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # save token for next time
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── BUILD EMAIL ──────────────────────────────────────────

def build_email(
    to: str,
    subject: str,
    body: str,
    from_name: str = "PlacementAI"
) -> dict:
    """Build a MIME email message ready to send"""
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject

    # plain text version
    text_part = MIMEText(body, "plain")
    message.attach(text_part)

    # encode for Gmail API
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


# ─── SEND EMAIL ───────────────────────────────────────────

def send_email(
    to: str,
    subject: str,
    body: str,
    job_id: str = None
) -> bool:
    """
    Send a cold email via Gmail API
    returns True if sent, False if failed
    """
    try:
        service = get_gmail_service()
        if not service:
            print("❌ Gmail service not available")
            return False

        message = build_email(to, subject, body)

        sent = service.users().messages().send(
            userId="me",
            body=message
        ).execute()

        print(f"✅ Email sent to {to} — message ID: {sent['id']}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


# ─── PREVIEW (without sending) ───────────────────────────

def preview_email(to: str, subject: str, body: str):
    """Print email preview — use this to check before sending"""
    print(f"\n{'='*60}")
    print(f"📧 EMAIL PREVIEW")
    print(f"{'='*60}")
    print(f"To:      {to}")
    print(f"Subject: {subject}")
    print(f"{'─'*60}")
    print(body)
    print(f"{'='*60}\n")


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing email_sender.py...\n")

    if not GMAIL_AVAILABLE:
        print("Install Gmail API libraries first:")
        print("pip install google-auth google-auth-oauthlib google-api-python-client")
        exit()

    # preview test — doesn't actually send
    preview_email(
        to="recruiter@razorpay.com",
        subject="Full Stack Internship at Razorpay — Riya Sharma",
        body="""Hi Shobana,

I came across the Full Stack Development Intern role at Razorpay and wanted to reach out directly.

Razorpay's work on payment infrastructure for Indian businesses is genuinely exciting — I've used the APIs myself in a project.

I'm a 3rd year CS student with strong experience in React, Node.js, and Python. I recently built a full-stack expense tracker and contributed to two open source projects.

I'd love to be considered for this role — I've attached my resume and my GitHub is github.com/riya.

Would you be open to a quick chat?

Riya Sharma"""
    )

    print("✅ Preview works — email not actually sent")
    print("\nTo send for real:")
    print("1. Set up Gmail credentials (google cloud console)")
    print("2. Call send_email(to, subject, body)")