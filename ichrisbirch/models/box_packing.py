from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base


class Box(Base):
    """SQLAlchemy model for box_packing.boxes table"""

    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'boxes'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(String, nullable=False)
    essential = Column(Boolean)
    warm = Column(Boolean)
    liquid = Column(Boolean)
    items = relationship('Item', back_populates='box', cascade='all, delete')

    def __repr__(self):
        return f'''Box(name={self.name!r}, size={self.size!r}, essential={self.essential!r},
            warm={self.warm!r}, liquid={self.liquid!r})'''


class Item(Base):
    """SQLAlchemy model for box_packing.items table"""

    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    box_id = Column(Integer, ForeignKey('box_packing.boxes.id'), nullable=False)
    name = Column(String, nullable=False)
    essential = Column(Boolean, nullable=False)
    warm = Column(Boolean, nullable=False)
    liquid = Column(Boolean, nullable=False)
    box = relationship('Box', back_populates='items')

    def __repr__(self):
        return f'''Item(box_id={self.box_id!r}, name={self.name!r}, essential={self.essential!r},
            warm={self.warm!r}, liquid={self.liquid!r})'''
