from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ichrisbirch.schemas.not_null import NotNull
from ichrisbirch.schemas.task import WindowDays


class AutoTaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AutoTaskCreate(AutoTaskConfig):
    name: str
    notes: str | None = None
    category: str
    frequency: str
    window_days: WindowDays | None = Field(
        None, description="Days each copy gets before it sorts as due. The category's window when omitted."
    )
    anchor: str = 'completion'
    max_concurrent: int | None = None


class AutoTask(AutoTaskConfig):
    id: int
    name: str
    category: str
    notes: str | None = None
    frequency: str
    window_days: int | None = None
    anchor: str
    max_concurrent: int
    first_run_date: datetime
    last_run_date: datetime
    run_count: int


class AutoTaskUpdate(AutoTaskConfig):
    name: NotNull[str] = None
    category: NotNull[str] = None
    notes: str | None = None
    frequency: NotNull[str] = None
    window_days: WindowDays | None = None
    anchor: NotNull[str] = None
    max_concurrent: NotNull[int] = None
