from euphoria import db
from datetime import datetime


class Task(db.Model):
    """Data Model for Priority Tasks"""

    __table_args__ = {'schema': 'tasks'}
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    category = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory1 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory2 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    priority = db.Column(db.Integer, index=False, unique=False, nullable=False)
    add_date = db.Column(
        db.DateTime(),
        index=False,
        unique=False,
        nullable=False,
        default=datetime.now(),
    )
    complete_date = db.Column(
        db.DateTime(), index=False, unique=False, nullable=True
    )

    def __repr__(self):
        return f'Task(name = {self.name}, priority = {self.priority}, category = {self.category}, subcategory1 = {self.subcategory1}, subcategory2 = {self.subcategory2}, , add_date = {self.add_date}, complete_date = {self.complete_date})'

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
