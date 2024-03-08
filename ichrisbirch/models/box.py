import enum

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ichrisbirch.database.sqlalchemy.base import Base


class BoxSize(enum.Enum):
    """Enum for box sizes"""

    BOOK = 'BOOK'
    SMALL = 'SMALL'
    MEDIUM = 'MEDIUM'
    LARGE = 'LARGE'
    BAG = 'BAG'
    MONITOR = 'MONITOR'
    MISC = 'MISC'


class Box(Base):
    """SQLAlchemy model for box_packing.boxes table"""

    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'boxes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[BoxSize] = mapped_column(Enum(BoxSize), nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean)
    warm: Mapped[bool] = mapped_column(Boolean)
    liquid: Mapped[bool] = mapped_column(Boolean)
    items = relationship('BoxItem', back_populates='box', cascade='all, delete')

    def __repr__(self):
        return f'''Box(id={self.id}, name={self.name}, size={self.size}, essential={self.essential},
            warm={self.warm}, liquid={self.liquid})'''
