from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SchedulerJobRunCreate(SchedulerConfig):
    job_id: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    success: bool
    error_type: str | None = None
    error_message: str | None = None


class SchedulerJobRun(SchedulerConfig):
    id: int
    job_id: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    success: bool
    error_type: str | None = None
    error_message: str | None = None
