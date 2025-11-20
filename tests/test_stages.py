import json
from pathlib import Path

import pytest

from backend.pipeline import stages
from backend.pipeline.models import Job


def test_transcript_to_srt(tmp_path: Path):
    transcript = tmp_path / "sample.json"
    with open(transcript, "w") as f:
        json.dump({"segments": [{"start": 0, "end": 2.5, "text": "Hello world"}]}, f)

    srt = stages.transcript_to_srt(transcript)
    assert srt.exists()
    content = srt.read_text()
    assert "00:00:00,000 --> 00:00:02,500" in content
    assert "Hello world" in content


def test_run_pipeline_success(monkeypatch, tmp_path: Path):
    job = Job(job_id="123", url="https://example.com")
    stages.initialize_job(job)

    dummy_video = tmp_path / "source.mp4"
    dummy_video.touch()
    dummy_audio = tmp_path / "audio.wav"
    dummy_audio.touch()
    dummy_video_silent = tmp_path / "video_silent.mp4"
    dummy_video_silent.touch()
    vocals = tmp_path / "vocals.wav"
    vocals.touch()
    accompaniment = tmp_path / "accompaniment.wav"
    transcript_json = tmp_path / "vocals.json"
    with open(transcript_json, "w") as f:
        json.dump({"segments": []}, f)

    def fake_download(url, workdir):
        return dummy_video

    def fake_extract(video, workdir):
        return {"audio": dummy_audio, "video": dummy_video_silent}

    def fake_separate(audio, workdir):
        return {"vocals": vocals, "accompaniment": accompaniment}

    def fake_transcribe(audio, workdir):
        return transcript_json

    def fake_merge(video, audio, workdir):
        merged = tmp_path / "merged.mp4"
        merged.touch()
        return merged

    def fake_overlay(video, srt, workdir):
        final = tmp_path / "final.mp4"
        final.touch()
        return final

    monkeypatch.setattr(stages, "download_video", fake_download)
    monkeypatch.setattr(stages, "extract_streams", fake_extract)
    monkeypatch.setattr(stages, "separate_vocals", fake_separate)
    monkeypatch.setattr(stages, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(stages, "transcript_to_srt", lambda p: tmp_path / "lyrics.srt")
    monkeypatch.setattr(stages, "merge_audio_video", fake_merge)
    monkeypatch.setattr(stages, "overlay_subtitles", fake_overlay)

    stages.run_pipeline(job, tmp_path)

    assert job.status == "completed"
    assert job.output_file.endswith("final.mp4")
    assert all(stage.status == "success" for stage in job.stages.values())


def test_run_pipeline_handles_failure(monkeypatch, tmp_path: Path):
    job = Job(job_id="123", url="https://example.com")
    stages.initialize_job(job)

    def failing_download(url, workdir):
        raise RuntimeError("download failed")

    monkeypatch.setattr(stages, "download_video", failing_download)

    stages.run_pipeline(job, tmp_path)

    assert job.status == "failed"
    assert job.error == "download failed"
    assert job.stages["download"].status == "failed"
