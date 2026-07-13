# scheduler.py — runs agent.py automatically every X hours
# also exposes a manual trigger function

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from agent import run_agent
from db import get_config

scheduler = BackgroundScheduler()


def scheduled_job():
    """Wrapper that runs the agent and logs the time"""
    print(f"\n⏰ Scheduled run triggered at {datetime.now().strftime('%H:%M:%S')}")
    try:
        run_agent(max_pages=15)
    except Exception as e:
        print(f"❌ Scheduled run failed: {e}")


def start_scheduler():
    """
    Start the background scheduler
    reads interval from your config (default 4 hours)
    """
    config = get_config()
    interval_hours = config.agent_interval_hours if config else 2

    scheduler.add_job(
        scheduled_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id="agent_job",
        replace_existing=True,
        next_run_time=datetime.now()  # run once immediately on startup
    )

    scheduler.start()
    print(f"✅ Scheduler started — agent will run every {interval_hours} hours")
    print(f"   First run starting now...")


def stop_scheduler():
    """Stop the scheduler gracefully"""
    scheduler.shutdown()
    print("🛑 Scheduler stopped")


def trigger_now():
    """Manually trigger an agent run right now, outside the schedule"""
    print(f"\n🔥 Manual trigger requested at {datetime.now().strftime('%H:%M:%S')}")
    return run_agent(max_pages=15)


def update_interval(new_hours: int):
    """Change how often the agent runs — call this if config changes"""
    scheduler.reschedule_job(
        "agent_job",
        trigger=IntervalTrigger(hours=new_hours)
    )
    print(f"✅ Schedule updated — now runs every {new_hours} hours")

def cleanup_old_jobs():
    """Delete jobs older than 30 days to keep DB lean"""
    try:
        from db import supabase
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        supabase.table("jobs")\
            .delete()\
            .in_("status", ["skipped", "applied", "emailed"])\
            .lt("created_at", cutoff)\
            .execute()
        print("🧹 Cleaned up old jobs")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

# add this alongside your existing scheduler job in start_scheduler()
scheduler.add_job(
    cleanup_old_jobs,
    trigger=IntervalTrigger(days=1),  # runs once a day
    id="cleanup_job",
    replace_existing=True
)


# ─── TEST ─────────────────────────────────────────────────

if __name__ == "__main__":
    import time

    print("Testing scheduler.py...\n")
    print("Starting scheduler (will run agent immediately, then every 2 hours)")
    print("Press Ctrl+C to stop\n")

    start_scheduler()

    try:
        # keep the script alive to let scheduler run
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
        print("\nStopped by user")