from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from ichrisbirch.database.sqlalchemy.base import Base


class JournalEntry(Base):
    """SQLAlchemy model for journal table"""

    __tablename__ = 'journal'
    id = Column(Integer, primary_key=True)
    title = Column(String())
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content = Column(String())
    feeling = Column(Integer, nullable=False)
