from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HabitCategory(HabitConfig):
    id: int
    name: str
    is_current: bool


class HabitCategoryCreate(HabitConfig):
    name: str
    is_current: bool = True


class HabitCategoryUpdate(HabitConfig):
    name: str | None = None
    is_current: bool | None = None


