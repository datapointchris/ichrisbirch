from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.habitcategory import HabitCategory


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HabitCompleted(HabitConfig):
    id: int
    habit_id: int | None = None
    name: str
    category_id: int
    category: HabitCategory
    complete_date: datetime


class HabitCompletedCreate(HabitConfig):
    """habit_id is optional so historical imports and completions of a
    since-deleted habit still record; a caller that knows the habit sends it."""

    habit_id: int | None = None
    name: str
    category_id: int
    complete_date: datetime
