# tray.py — system tray icon + native OS notifications
# polls backend every 30 min, fires notification on new jobs
# runs silently in background, auto-starts on login

import pystray
from PIL import Image, ImageDraw
from plyer import notification
import requests
import threading
import time
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LOCAL_UI_URL = "http://localhost:5001/jobs"
POLL_INTERVAL = 1800  # 30 minutes

seen_job_ids = set()


# ─── CREATE TRAY ICON IMAGE ──────────────────────────────

def create_icon_image():
    """Simple generated icon — a blue circle with a dot"""
    img = Image.new("RGB", (64, 64), color="white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill="#534AB7")
    draw.ellipse((24, 24, 40, 40), fill="white")
    return img


# ─── CHECK FOR NEW JOBS ───────────────────────────────────

def check_new_jobs():
    """Poll backend for new jobs, fire notification if found"""
    global seen_job_ids
    try:
        res = requests.get(f"{BACKEND_URL}/jobs/new", timeout=10)
        data = res.json()
        jobs = data.get("jobs", [])

        new_jobs = [j for j in jobs if j["id"] not in seen_job_ids]

        if new_jobs:
            for job in new_jobs:
                seen_job_ids.add(job["id"])

            top_job = max(new_jobs, key=lambda j: j["score"])

            if len(new_jobs) == 1:
                title = f"New opening — {top_job['company']}"
                message = f"{top_job['role']} · Score {top_job['score']}/10"
            else:
                title = f"{len(new_jobs)} new openings found"
                message = f"Top match: {top_job['company']} — {top_job['role']} ({top_job['score']}/10)"

            notification.notify(
                title=title,
                message=message,
                app_name="PlacementAI",
                timeout=10
            )
            print(f"🔔 Notified about {len(new_jobs)} new job(s)")
        else:
            print(f"   No new jobs this check ({len(jobs)} total in queue)")

    except Exception as e:
        print(f"⚠️  Could not check jobs: {e}")


# ─── BACKGROUND POLLING LOOP ──────────────────────────────

def polling_loop():
    """Runs forever, checks for jobs every POLL_INTERVAL seconds"""
    print(f"🔄 Polling started — checking every {POLL_INTERVAL // 60} min")
    while True:
        check_new_jobs()
        time.sleep(POLL_INTERVAL)


# ─── TRAY MENU ACTIONS ─────────────────────────────────────

def open_jobs_page(icon, item):
    webbrowser.open(LOCAL_UI_URL)


def run_now(icon, item):
    """Manually trigger agent run"""
    try:
        notification.notify(
            title="PlacementAI",
            message="Running search now... this may take a minute",
            app_name="PlacementAI",
            timeout=5
        )
        requests.post(f"{BACKEND_URL}/agent/run", timeout=300)
        check_new_jobs()
    except Exception as e:
        print(f"⚠️  Run now failed: {e}")


def check_now(icon, item):
    """Just check for new jobs without running the full agent"""
    check_new_jobs()


def quit_app(icon, item):
    icon.stop()


# ─── BUILD TRAY ICON ───────────────────────────────────────

def main():
    icon_image = create_icon_image()

    menu = pystray.Menu(
        pystray.MenuItem("View new jobs", open_jobs_page, default=True),
        pystray.MenuItem("Check now", check_now),
        pystray.MenuItem("Run full search now", run_now),
        pystray.MenuItem("Quit", quit_app)
    )

    icon = pystray.Icon("PlacementAI", icon_image, "PlacementAI", menu)

    # start polling in background thread
    poll_thread = threading.Thread(target=polling_loop, daemon=True)
    poll_thread.start()

    print("✅ PlacementAI tray icon running")
    print("   Right-click the icon in your taskbar for options")

    icon.run()


if __name__ == "__main__":
    main()