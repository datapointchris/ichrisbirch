from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

from ichrisbirch.schemas.habitcategory import HabitCategory

EASTERNMOST_UTC_OFFSET = timedelta(hours=14)


class HabitConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HabitCompleted(HabitConfig):
    id: int
    habit_id: int | None = None
    name: str
    category_id: int
    category: HabitCategory
    complete_date: date


class HabitCompletedCreate(HabitConfig):
    """habit_id is optional so historical imports and completions of a
    since-deleted habit still record; a caller that knows the habit sends it."""

    habit_id: int | None = None
    name: str
    category_id: int
    complete_date: date

    @field_validator('complete_date')
    @classmethod
    def complete_date_has_started_somewhere(cls, v: date) -> date:
        """A habit cannot be recorded for a day that has not begun yet.

        A schema validator has no user to read a zone from, so the bound is the
        latest today anywhere: UTC+14, in the Line Islands. A later day has not
        started for anyone, and an earlier one has started for someone.
        """
        if v > (datetime.now(UTC) + EASTERNMOST_UTC_OFFSET).date():
            raise ValueError('complete_date is in the future')
        return v
