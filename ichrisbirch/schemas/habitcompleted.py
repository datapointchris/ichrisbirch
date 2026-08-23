from datetime import UTC
from datetime import datetime
from datetime import timedelta

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

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

    @field_validator('complete_date')
    @classmethod
    def complete_date_is_not_ahead_of_now(cls, v: datetime) -> datetime:
        """A habit cannot be recorded before it has been done.

        The margin is a day rather than zero. A client stamps the day it is filling
        in at its own local noon, and a zone far enough east of UTC puts that ahead
        of UTC now while still being that client's today. A day is wider than any
        real offset and still refuses a date typed years out.
        """
        moment = v if v.tzinfo else v.replace(tzinfo=UTC)
        if moment > datetime.now(UTC) + timedelta(days=1):
            raise ValueError('complete_date is in the future')
        return v
