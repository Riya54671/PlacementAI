# main.py — FastAPI app, ties everything together

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import jobs, settings, recruiter, email, sheets
from scheduler import start_scheduler, stop_scheduler, trigger_now
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

@app.get("/")
@app.head("/")
def root():
    return {"status": "running", "message": "PlacementAI backend is alive"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting PlacementAI backend...")
    start_scheduler()
    yield
    print("🛑 Shutting down...")
    stop_scheduler()


app = FastAPI(title="PlacementAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# register all routes — must be after app = FastAPI()
app.include_router(jobs.router)
app.include_router(settings.router)
app.include_router(recruiter.router)
app.include_router(email.router)
app.include_router(sheets.router)


@app.get("/")
def root():
    return {"status": "running", "message": "PlacementAI backend is alive"}


@app.post("/agent/run")
def manual_trigger():
    """Manually trigger an agent run right now"""
    result = trigger_now()
    return {
        "jobs_found": result.jobs_found,
        "jobs_saved": result.jobs_saved,
        "errors": result.errors,
        "duration_seconds": result.duration_seconds
    }