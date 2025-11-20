import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import ffmpeg

from backend.config import STAGES
from backend.pipeline.models import Job, StageResult


def run_command(command: list, cwd: Path | None = None) -> Tuple[bool, str]:
    """Execute shell command and return success flag and combined output."""
    process = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    success = process.returncode == 0
    output = (process.stdout or "") + (process.stderr or "")
    return success, output


def initialize_job(job: Job):
    for stage in STAGES:
        job.stages[stage] = StageResult(name=stage)


def mark_stage(job: Job, stage: str, status: str, message: str = "", output: str | None = None):
    stage_ref = job.stages[stage]
    if status == "running":
        stage_ref.started_at = datetime.utcnow()
    if status in {"success", "failed"}:
        stage_ref.finished_at = datetime.utcnow()
    stage_ref.status = status
    stage_ref.message = message
    stage_ref.output = output


def download_video(url: str, workdir: Path) -> Path:
    output_path = workdir / "source.mp4"
    command = [
        "yt-dlp",
        "-o",
        str(output_path),
        url,
    ]
    success, output = run_command(command)
    if not success:
        raise RuntimeError(f"Failed to download video: {output}")
    return output_path


def extract_streams(video_path: Path, workdir: Path) -> Dict[str, Path]:
    audio_path = workdir / "audio.wav"
    video_no_audio = workdir / "video_silent.mp4"

    audio_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-q:a",
        "0",
        "-map",
        "a",
        str(audio_path),
    ]
    success, output = run_command(audio_cmd)
    if not success:
        raise RuntimeError(f"Audio extraction failed: {output}")

    video_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-an",
        str(video_no_audio),
    ]
    success, output = run_command(video_cmd)
    if not success:
        raise RuntimeError(f"Video extraction failed: {output}")

    return {"audio": audio_path, "video": video_no_audio}


def separate_vocals(audio_path: Path, workdir: Path) -> Dict[str, Path]:
    output_dir = workdir / "spleeter"
    output_dir.mkdir(exist_ok=True)
    command = [
        "spleeter",
        "separate",
        "-p",
        "spleeter:2stems",
        "-o",
        str(output_dir),
        str(audio_path),
    ]
    success, output = run_command(command)
    if not success:
        raise RuntimeError(f"Spleeter failed: {output}")

    # Spleeter creates subdir named after input file stem
    track_dir = output_dir / audio_path.stem
    return {
        "vocals": track_dir / "vocals.wav",
        "accompaniment": track_dir / "accompaniment.wav",
    }


def transcribe_audio(audio_path: Path, workdir: Path) -> Path:
    transcript_dir = workdir / "transcript"
    transcript_dir.mkdir(exist_ok=True)
    command = [
        "whisper",
        str(audio_path),
        "--model",
        "base",
        "--output_format",
        "json",
        "--output_dir",
        str(transcript_dir),
    ]
    success, output = run_command(command)
    if not success:
        raise RuntimeError(f"Transcription failed: {output}")

    # Whisper outputs json with same stem
    return transcript_dir / f"{audio_path.stem}.json"


def transcript_to_srt(json_path: Path) -> Path:
    srt_path = json_path.with_suffix(".srt")
    with open(json_path) as f:
        data = json.load(f)
    lines = []
    for index, segment in enumerate(data.get("segments", []), start=1):
        start = segment.get("start", 0)
        end = segment.get("end", start)
        text = segment.get("text", "").strip()
        lines.append(
            f"{index}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n\n"
        )
    with open(srt_path, "w") as f:
        f.writelines(lines)
    return srt_path


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    milliseconds = int((secs - int(secs)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{milliseconds:03d}"


def merge_audio_video(video_path: Path, audio_path: Path, workdir: Path) -> Path:
    merged_path = workdir / "karaoke_base.mp4"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(merged_path),
    ]
    success, output = run_command(command)
    if not success:
        raise RuntimeError(f"Failed to merge audio/video: {output}")
    return merged_path


def overlay_subtitles(video_path: Path, srt_path: Path, workdir: Path) -> Path:
    output_path = workdir / "karaoke_final.mp4"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"subtitles={srt_path}",
        "-c:a",
        "copy",
        str(output_path),
    ]
    success, output = run_command(command)
    if not success:
        raise RuntimeError(f"Failed to overlay subtitles: {output}")
    return output_path


def run_pipeline(job: Job, workdir: Path):
    # Stage 1: Download
    mark_stage(job, "download", "running")
    try:
        video_path = download_video(job.url, workdir)
        mark_stage(job, "download", "success", message="Video downloaded", output=str(video_path))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "download", "failed", message=str(exc))
        job.error = str(exc)
        return

    # Stage 2: Extract
    mark_stage(job, "extract", "running")
    try:
        extracted = extract_streams(video_path, workdir)
        mark_stage(job, "extract", "success", message="Audio/Video separated", output=json.dumps({k: str(v) for k, v in extracted.items()}))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "extract", "failed", message=str(exc))
        job.error = str(exc)
        return

    # Stage 3: Separate vocals
    mark_stage(job, "separate_vocals", "running")
    try:
        stems = separate_vocals(extracted["audio"], workdir)
        mark_stage(job, "separate_vocals", "success", message="Vocals removed", output=json.dumps({k: str(v) for k, v in stems.items()}))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "separate_vocals", "failed", message=str(exc))
        job.error = str(exc)
        return

    # Stage 4: Transcribe vocals
    mark_stage(job, "transcribe", "running")
    try:
        transcript_json = transcribe_audio(stems["vocals"], workdir)
        srt_path = transcript_to_srt(transcript_json)
        mark_stage(job, "transcribe", "success", message="Transcript generated", output=str(srt_path))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "transcribe", "failed", message=str(exc))
        job.error = str(exc)
        return

    # Stage 5: Merge audio/video with accompaniment
    mark_stage(job, "merge", "running")
    try:
        merged = merge_audio_video(extracted["video"], stems["accompaniment"], workdir)
        mark_stage(job, "merge", "success", message="Instrumental merged", output=str(merged))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "merge", "failed", message=str(exc))
        job.error = str(exc)
        return

    # Stage 6: Overlay subtitles
    mark_stage(job, "overlay", "running")
    try:
        final_path = overlay_subtitles(merged, srt_path, workdir)
        job.output_file = str(final_path)
        mark_stage(job, "overlay", "success", message="Karaoke video ready", output=str(final_path))
    except Exception as exc:  # noqa: BLE001
        mark_stage(job, "overlay", "failed", message=str(exc))
        job.error = str(exc)
        return
