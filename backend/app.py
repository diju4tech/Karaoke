from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import STATIC_DIR
from backend.pipeline.worker import get_manager_singleton

app = FastAPI(title="Karaoke Generator", version="1.0.0")
manager = get_manager_singleton()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/jobs")
def create_job(payload: dict):
    url: Optional[str] = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    job = manager.create_job(url)
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.output_file:
        raise HTTPException(status_code=400, detail="Job not finished")
    return FileResponse(Path(job.output_file), filename=f"karaoke-{job_id}.mp4")


# Static frontend
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
