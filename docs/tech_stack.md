# Technology Stack

## Backend
- **FastAPI** for HTTP API endpoints and static file hosting.
- **Threaded job manager** with an in-memory queue to serialize pipeline execution locally.
- **yt-dlp** downloads YouTube videos.
- **ffmpeg** extracts streams, merges audio/video, and overlays subtitles.
- **Spleeter** performs 2-stem vocal separation to obtain instrumental backing.
- **Whisper (CLI)** generates transcripts with word-level timestamps.

## Pipeline Design
- Each stage has a dedicated function and shared `StageResult` tracking.
- Fail-fast per stage with detailed error messages propagated to the job status.
- Job directories under `data/jobs/<job_id>` store all intermediate and final artifacts.
- Transcript JSON is converted to SRT for subtitle overlays.

## Frontend
- Static HTML + Vanilla JS single page with status polling.
- Minimal CSS for badge-based stage visualization and download call-to-action.

## Container Structure
- **Dockerfile** installs system dependencies (ffmpeg) and Python requirements.
- **docker-compose.yml** builds the backend image, mounts `./data` for artifacts, and exposes port 8000.
- Frontend assets are served by FastAPI from the `frontend` directory baked into the container image.
