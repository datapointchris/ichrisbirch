# Base needs the models imported before being used by Alembic
from sqlalchemy.orm import declarative_base

from ....common.models.apartments import Apartment
from ....common.models.box_packing import Box, Item
from ....common.models.countdowns import Countdown
from ....common.models.events import Event
from ....common.models.habits import Habit
from ....common.models.journal import JournalEntry

# from ....common.models.portfolio import Portfolio
from ....common.models.tasks import Task


Base = declarative_base()
