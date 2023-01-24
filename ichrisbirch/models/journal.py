from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, DateTime
from ichrisbirch.db.sqlalchemy.base import Base


class JournalEntry(Base):
    __tablename__ = 'journal'
    id = Column(Integer, primary_key=True)
    title = Column(String())
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content = Column(String())
    feeling = Column(Integer, nullable=False)
