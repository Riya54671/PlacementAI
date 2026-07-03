# app.py — local Flask server
# shows your job feed at localhost:5001/jobs
# talks to your Railway/local backend via REST

from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@app.route("/")
def home():
    """Redirect to jobs page"""
    return jobs_page()


@app.route("/jobs")
def jobs_page():
    """Show all new jobs as cards"""
    try:
        res = requests.get(f"{BACKEND_URL}/jobs/new", timeout=10)
        data = res.json()
        jobs = data.get("jobs", [])
    except Exception as e:
        print(f"❌ Could not reach backend: {e}")
        jobs = []

    return render_template("jobs.html", jobs=jobs, count=len(jobs))


@app.route("/jobs/skip", methods=["POST"])
def skip_job():
    """Mark a job as skipped"""
    job_id = request.json.get("job_id")
    try:
        requests.post(f"{BACKEND_URL}/jobs/skip", json={"job_id": job_id}, timeout=10)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/jobs/approve", methods=["POST"])
def approve_job():
    """Mark a job as applied"""
    job_id = request.json.get("job_id")
    try:
        requests.post(f"{BACKEND_URL}/jobs/approve", json={"job_id": job_id}, timeout=10)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/run-now", methods=["POST"])
def run_now():
    """Trigger an immediate agent run"""
    try:
        res = requests.post(f"{BACKEND_URL}/agent/run", timeout=300)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/sheets/update", methods=["POST"])
def sheets_update():
    """Forward sheets status update to backend"""
    data = request.json
    try:
        requests.post(
            f"{BACKEND_URL}/sheets/update",
            json=data,
            timeout=10
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    print("🌐 Starting local jobs page at http://localhost:5001/jobs")
    app.run(port=5001, debug=True)