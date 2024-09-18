import enum

from sqlalchemy import Boolean
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.sqlalchemy.base import Base


class BoxSize(enum.Enum):
    Book = 'Book'
    Small = 'Small'
    Medium = 'Medium'
    Large = 'Large'
    Bag = 'Bag'
    Monitor = 'Monitor'
    Misc = 'Misc'
    Sixteen = 'Sixteen'


class Box(Base):
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
