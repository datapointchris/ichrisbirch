from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship
from ..db.sqlalchemy.base_class import Base


class Box(Base):
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
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    box_id = Column(Integer, ForeignKey('boxes.id'), nullable=False)
    name = Column(String, nullable=False)
    essential = Column(Boolean, nullable=False)
    warm = Column(Boolean, nullable=False)
    liquid = Column(Boolean, nullable=False)
    box = relationship('Box', back_populates='items')

    def __repr__(self):
        return f'''Item(box_id={self.box_id!r}, name={self.name!r}, essential={self.essential!r},
            warm={self.warm!r}, liquid={self.liquid!r})'''
