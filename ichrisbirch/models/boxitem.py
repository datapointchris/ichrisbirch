from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base


class BoxItem(Base):
    __table_args__ = {'schema': 'box_packing'}
    __tablename__ = 'items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    box_id: Mapped[int] = mapped_column(Integer, ForeignKey('box_packing.boxes.id', ondelete='SET NULL'), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean, nullable=False)
    warm: Mapped[bool] = mapped_column(Boolean, nullable=False)
    liquid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    box = relationship('Box', back_populates='items')

    def __repr__(self):
        return f"""Item(id={self.id}, box_id={self.box_id}, name={self.name}, essential={self.essential},
            warm={self.warm}, liquid={self.liquid})"""
