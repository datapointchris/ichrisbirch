from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, DateTime
from ..db.sqlalchemy import Base


class Task(Base):
    """Data Model for Priority Tasks"""

    __table_args__ = {'schema': 'tasks'}
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    category = Column(String(64))
    priority = Column(Integer, nullable=False)
    add_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    complete_date = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f''''Task(name = {self.name}, priority = {self.priority}, category = {self.category},
            add_date = {self.add_date}, complete_date = {self.complete_date})'''

    @property
    def days_to_complete(self):
        if self.complete_date:
            return (self.complete_date - self.add_date).days + 1
        return None

    @property
    def weeks_to_complete(self):
        if self.complete_date:
            total_days = self.days_to_complete
            weeks, days = divmod(total_days, 7)
            return f'{weeks} weeks, {days} days'
        return None


def calculate_average_completion_time(completed: list[Task]) -> str:
    if not completed:
        return 'No tasks completed for this time period'
    total_days = sum(task.days_to_complete for task in completed)
    average_days = total_days / len(completed)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'
