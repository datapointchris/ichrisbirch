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


class HabitCreate(HabitConfig):
    name: str
    category_id: int
    is_current: bool = True


class Habit(HabitConfig):
    id: int
    name: str
    category_id: int
    category: HabitCategory
    is_current: bool


class HabitUpdate(HabitConfig):
    name: str | None = None
    category_id: int | None = None
    is_current: bool | None = None


class HabitCompleted(HabitConfig):
    id: int
    name: str
    category_id: int
    category: HabitCategory
    complete_date: datetime


class HabitCompletedCreate(HabitConfig):
    name: str
    category_id: int
    complete_date: datetime
