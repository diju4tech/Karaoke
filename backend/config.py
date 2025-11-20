import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("KARAOKE_DATA", "./data"))
JOBS_DIR = DATA_DIR / "jobs"
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Stage constants
STAGES = [
    "download",
    "extract",
    "separate_vocals",
    "transcribe",
    "merge",
    "overlay",
]

# Ensure directories exist at import time
JOBS_DIR.mkdir(parents=True, exist_ok=True)
