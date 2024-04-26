from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HabitCreate(HabitConfig):
    name: str
    category_id: int
    is_current: bool


class Habit(HabitConfig):
    id: int
    name: str
    category_id: int
    is_current: bool


class HabitUpdate(HabitConfig):
    name: str | None = None
    category_id: int | None = None
    is_current: bool | None = None


class HabitCompleted(HabitConfig):
    id: int
    name: str
    category_id: int
    complete_date: datetime


class HabitCompletedCreate(HabitConfig):
    name: str
    category_id: int
    complete_date: datetime


class HabitCategory(HabitConfig):
    id: int
    name: str


class HabitCategoryCreate(HabitConfig):
    name: str
