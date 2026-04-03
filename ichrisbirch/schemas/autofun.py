from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class AutoFunConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AutoFunCreate(AutoFunConfig):
    name: str
    notes: str | None = None


class AutoFun(AutoFunConfig):
    id: int
    name: str
    notes: str | None = None
    is_completed: bool
    completed_date: datetime | None = None
    added_date: datetime


class AutoFunUpdate(AutoFunConfig):
    name: str | None = None
    notes: str | None = None
