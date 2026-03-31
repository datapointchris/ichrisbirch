from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

BOX_SIZES = [
    'Bag',
    'Book',
    'Large',
    'Medium',
    'Misc',
    'Monitor',
    'Sixteen',
    'Small',
    'UhaulSmall',
]


class BoxSize(Base):
    """Lookup table for valid box sizes, replacing PostgreSQL ENUM type."""

    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'box_sizes'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Box(Base):
    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'boxes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    size: Mapped[str] = mapped_column(Text, ForeignKey('box_packing.box_sizes.name'), nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean)
    warm: Mapped[bool] = mapped_column(Boolean)
    liquid: Mapped[bool] = mapped_column(Boolean)
    items = relationship('BoxItem', back_populates='box')

    def __repr__(self):
        return f"""Box(id={self.id}, name={self.name}, size={self.size}, essential={self.essential},
            warm={self.warm}, liquid={self.liquid})"""
