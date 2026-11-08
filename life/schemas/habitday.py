import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict

from life.schemas.habit import Habit
from life.schemas.habitcompleted import HabitCompleted


class HabitsDay(BaseModel):
    """One day's habits board, already split and ordered.

    `date` and `timezone` echo what the day was resolved against, so a caller
    that sent neither can see which day it got rather than assuming its own.
    """

    model_config = ConfigDict(from_attributes=True)

    date: dt.date
    timezone: str
    due: list[Habit]
    completed: list[HabitCompleted]
    current_total: int
