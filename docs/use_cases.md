# Use Cases

## End-User Flow
1. User opens the web UI served locally.
2. Pastes a YouTube URL and clicks **Start Processing**.
3. The backend creates a job and starts the pipeline stages.
4. The UI polls the status endpoint and updates stage badges.
5. When complete, the UI displays a download link for the karaoke video.

## Error Scenarios
- Invalid URL: backend returns 400; UI surfaces error.
- Download failure (network/DRM): job marks `download` failed and stops.
- Missing dependencies (ffmpeg/whisper/spleeter): stage fails with error message.
- Disk full: any stage can fail; error returned in status payload.

## System Actor Interactions
- **User** interacts with the UI to create jobs and download results.
- **Backend API** orchestrates the pipeline, persists files per job, and reports statuses.
- **Worker** pulls queued jobs, runs every stage sequentially, and writes outputs.
