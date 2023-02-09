from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ichrisbirch.db.sqlalchemy.base import Base


class PortfolioProject(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content = Column(String())
