from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from ichrisbirch.database.base import Base


class PortfolioProject(Base):
    """SQLAlchemy model for portfolio table."""

    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content = Column(String())
