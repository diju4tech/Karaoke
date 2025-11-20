from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class StageResult:
    name: str
    status: str = "pending"  # pending, running, success, failed
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: str = ""
    output: Optional[str] = None


@dataclass
class Job:
    job_id: str
    url: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    stages: Dict[str, StageResult] = field(default_factory=dict)
    output_file: Optional[str] = None
    error: Optional[str] = None

    def stage_order(self) -> List[str]:
        return list(self.stages.keys())

    @property
    def status(self) -> str:
        if self.error:
            return "failed"
        if all(stage.status == "success" for stage in self.stages.values()):
            return "completed"
        if any(stage.status == "running" for stage in self.stages.values()):
            return "running"
        return "pending"

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "url": self.url,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "error": self.error,
            "output_file": self.output_file,
            "stages": {
                name: {
                    "status": stage.status,
                    "started_at": stage.started_at.isoformat() if stage.started_at else None,
                    "finished_at": stage.finished_at.isoformat() if stage.finished_at else None,
                    "message": stage.message,
                    "output": stage.output,
                }
                for name, stage in self.stages.items()
            },
        }
