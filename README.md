# Local Karaoke Generator

A fully local, containerized application that transforms YouTube videos into downloadable karaoke videos by downloading, demuxing, removing vocals, transcribing lyrics, and overlaying subtitles.

## Features
- Single-page UI to submit a YouTube URL and track pipeline stages
- FastAPI backend with endpoints to start jobs, poll status, and download the result
- Modular pipeline: download → extract → separate vocals → transcribe → merge → overlay
- Local processing only: yt-dlp, ffmpeg, Spleeter, Whisper CLI
- Dockerized for reproducible local runs

## Getting Started

### Prerequisites
- Docker and docker-compose installed
- Sufficient disk space for video assets

### Run with Docker Compose
```bash
docker compose up --build
```
Then open http://localhost:8000 to access the UI.

### Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### API
- `POST /api/jobs` `{ "url": "https://..." }` → creates job
- `GET /api/jobs/{job_id}` → status payload with per-stage info
- `GET /api/jobs/{job_id}/download` → final karaoke MP4 (when complete)

## Testing
```bash
pytest
```

## Project Structure
```
backend/
  app.py              # FastAPI entrypoint
  config.py           # Shared paths and stage definitions
  pipeline/           # Job models, stages, and worker
frontend/
  index.html          # UI
  app.js              # Client-side logic
  styles.css          # Styling
docs/
  use_cases.md
  tech_stack.md
  CHANGELOG_TEMPLATE.md
```

## Screenshots
> Add screenshots of the UI after running locally.

## Example Intermediate Outputs
- `data/jobs/<job_id>/source.mp4` - Original downloaded video
- `data/jobs/<job_id>/audio.wav` - Extracted audio track
- `data/jobs/<job_id>/spleeter/*` - Vocal/instrument stems
- `data/jobs/<job_id>/transcript/*.json` - Whisper transcript output
- `data/jobs/<job_id>/karaoke_final.mp4` - Final karaoke video

## Notes
- Whisper and Spleeter are CPU-intensive; adjust Docker resources accordingly.
- All dependencies are open source and run locally; no external paid APIs are used.
