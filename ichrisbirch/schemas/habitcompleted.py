from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from ichrisbirch.schemas.habitcategory import HabitCategory


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


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
