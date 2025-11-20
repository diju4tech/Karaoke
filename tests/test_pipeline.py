from pathlib import Path

from fastapi.testclient import TestClient

from backend import app
from backend.pipeline import stages


def test_create_and_status_job(monkeypatch, tmp_path: Path):
    client = TestClient(app.app)

    def fake_run_pipeline(job, workdir):
        for name in stages.STAGES:
            stages.mark_stage(job, name, "running")
            stages.mark_stage(job, name, "success", message="ok")
        job.output_file = str(tmp_path / "result.mp4")
        Path(job.output_file).touch()

    monkeypatch.setattr(stages, "run_pipeline", fake_run_pipeline)

    response = client.post("/api/jobs", json={"url": "https://example.com"})
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    status = client.get(f"/api/jobs/{job_id}")
    assert status.status_code == 200
    data = status.json()
    assert data["status"] in {"running", "completed"}

    # wait for worker to finish
    app.manager.q.join()

    finished = client.get(f"/api/jobs/{job_id}")
    assert finished.status_code == 200
    assert finished.json()["status"] == "completed"

    download = client.get(f"/api/jobs/{job_id}/download")
    assert download.status_code == 200
