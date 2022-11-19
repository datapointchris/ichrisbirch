from sqlalchemy import Column, Integer, String, DateTime
from euphoria.backend.common.db.sqlalchemy.base import Base


class Countdown(Base):
    __tablename__ = 'countdowns'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'Countdown(name={self.name}, date={self.date}'
