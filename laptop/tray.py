# tray.py — system tray icon + native OS notifications

import pystray
from PIL import Image, ImageDraw
from win10toast import ToastNotifier
import requests
import threading
import time
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LOCAL_UI_URL = "http://localhost:5001/jobs"
POLL_INTERVAL = 1800   # 30 minutes
KEEPALIVE_INTERVAL = 600  # 10 minutes
toaster = ToastNotifier()

seen_job_ids = set()


def create_icon_image():
    img = Image.new("RGBA", (64, 64), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=(83, 74, 183, 255))
    draw.ellipse((22, 22, 42, 42), fill=(255, 255, 255, 255))
    return img


def keep_alive():
    """Ping Render every 10 min to prevent sleep"""
    while True:
        try:
            requests.get(f"{BACKEND_URL}/", timeout=30)
            print(f"   💓 Keep-alive ping sent")
        except Exception as e:
            print(f"   ⚠️  Keep-alive failed: {e}")
        time.sleep(KEEPALIVE_INTERVAL)

def notify_and_open(title: str, message: str):
    """Fire a Windows notification that opens jobs page when clicked"""
    toaster.show_toast(
        title,
        message,
        duration=10,
        threaded=True,
        callback_on_click=lambda: webbrowser.open(LOCAL_UI_URL)
    )

def check_new_jobs():
    """Poll backend for new jobs, fire notification if found"""
    global seen_job_ids
    try:
        print(f"   🔍 Checking for new jobs...")
        res = requests.get(
            f"{BACKEND_URL}/jobs/new",
            timeout=60  # long timeout for Render cold start
        )

        if res.status_code != 200:
            print(f"   ⚠️  Backend returned {res.status_code}")
            return

        data = res.json()
        jobs = data.get("jobs", [])

        # first run — just populate seen_ids, don't notify
        if not seen_job_ids:
            for job in jobs:
                seen_job_ids.add(job["id"])
            print(f"   📋 Initialised with {len(jobs)} existing jobs")
            return

        new_jobs = [j for j in jobs if j["id"] not in seen_job_ids]

        if new_jobs:
            for job in new_jobs:
                seen_job_ids.add(job["id"])

            top_job = max(new_jobs, key=lambda j: j["score"])

            if len(new_jobs) == 1:
                title = f"New opening — {top_job['company']}"
                message = f"{top_job['role']} · Score {top_job['score']}/10"
            else:
                title = f"{len(new_jobs)} new openings found!"
                message = f"Top: {top_job['company']} — {top_job['role']} ({top_job['score']}/10)"

            notify_and_open(title, message)
            print(f"🔔 Notified: {title}")
        else:
            print(f"   No new jobs ({len(jobs)} total in queue)")

    except requests.exceptions.Timeout:
        print(f"   ⚠️  Backend timeout — Render may be waking up, will retry")
    except Exception as e:
        print(f"   ⚠️  Could not check jobs: {e}")


def polling_loop():
    """Check for jobs every 30 minutes"""
    # first check immediately on startup
    check_new_jobs()
    while True:
        time.sleep(POLL_INTERVAL)
        check_new_jobs()


def open_jobs_page(icon, item):
    webbrowser.open(LOCAL_UI_URL)


def run_now(icon, item):
    try:
        toaster.show_toast(
            "PlacementAI",
            "Running search now... takes 2-3 minutes",
            duration=5,
            threaded=True
        )
        requests.post(f"{BACKEND_URL}/agent/run", timeout=300)
        time.sleep(5)
        check_new_jobs()
    except Exception as e:
        print(f"⚠️  Run now failed: {e}")


def check_now_menu(icon, item):
    check_new_jobs()


def quit_app(icon, item):
    icon.stop()


def main():
    icon_image = create_icon_image()

    menu = pystray.Menu(
        pystray.MenuItem("View new jobs", open_jobs_page, default=True),
        pystray.MenuItem("Check now", check_now_menu),
        pystray.MenuItem("Run full search", run_now),
        pystray.MenuItem("Quit", quit_app)
    )

    icon = pystray.Icon("PlacementAI", icon_image, "PlacementAI", menu)

    # start keep-alive thread
    alive_thread = threading.Thread(target=keep_alive, daemon=True)
    alive_thread.start()

    # start polling thread
    poll_thread = threading.Thread(target=polling_loop, daemon=True)
    poll_thread.start()

    print("✅ PlacementAI tray icon running")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Polling every {POLL_INTERVAL // 60} minutes")
    print(f"   Keep-alive every {KEEPALIVE_INTERVAL // 60} minutes")

    icon.run()


if __name__ == "__main__":
    main()