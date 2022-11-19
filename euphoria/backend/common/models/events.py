from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from euphoria.backend.common.db.sqlalchemy.base import Base


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    date = Column(DateTime, nullable=False)
    venue = Column(String(256), nullable=False)
    url = Column(Text, nullable=True)
    cost = Column(Float, nullable=False)
    attending = Column(Boolean, nullable=False)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f'''Event(name={self.name}, date={self.date}, url={self.url}, venue={self.venue},
            cost={self.cost}, attending={self.attending}, notes={self.notes}'''
