import datetime as dt
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict


class RecordChange(BaseModel):
    """One write to one row, and who made it. `changes` maps each column to its `old` and `new`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    changed_at: dt.datetime
    table_name: str
    record_id: str
    operation: str
    changes: dict[str, Any]
    actor: str | None
    request_id: str | None
    job_run_id: str | None
