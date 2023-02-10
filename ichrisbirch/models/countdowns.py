from sqlalchemy import Column, DateTime, Integer, String

from ichrisbirch.db.sqlalchemy.base import Base


class Countdown(Base):
    """SQLAlchemy model for countdowns table"""

    __tablename__ = 'countdowns'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'Countdown(name={self.name}, date={self.date}'
