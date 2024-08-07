from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.habitcategory import HabitCategory


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


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
