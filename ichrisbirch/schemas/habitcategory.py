from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


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
    name: NotNull[str] = None
    is_current: NotNull[bool] = None
