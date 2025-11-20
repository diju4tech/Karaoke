import queue
import threading
import uuid
from pathlib import Path
from typing import Dict

from backend.config import JOBS_DIR
from backend.pipeline.models import Job
from backend.pipeline.stages import initialize_job, run_pipeline


class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.q: queue.Queue[Job] = queue.Queue()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def create_job(self, url: str) -> Job:
        job_id = str(uuid.uuid4())
        job_dir = JOBS_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        job = Job(job_id=job_id, url=url)
        initialize_job(job)
        self.jobs[job_id] = job
        self.q.put(job)
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def _worker_loop(self):
        while True:
            job = self.q.get()
            workdir = Path(JOBS_DIR / job.job_id)
            try:
                run_pipeline(job, workdir)
            finally:
                self.q.task_done()


def get_manager_singleton():
    """Singleton accessor to ensure one manager per process."""
    global _manager  # type: ignore
    try:
        return _manager
    except NameError:
        _manager = JobManager()
        return _manager
