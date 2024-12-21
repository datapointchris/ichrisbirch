from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.sqlalchemy.base import Base

# from sqlalchemy.orm import relationship


class Book(Base):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(postgresql.ARRAY(Text), nullable=True)
    goodreads_url: Mapped[str] = mapped_column(Text, unique=True, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=True)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=True)
    sell_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    sell_price: Mapped[float] = mapped_column(Float, nullable=True)
    read_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    read_finish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    abandoned: Mapped[bool] = mapped_column(Boolean, nullable=True)
    location: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    # book_box = relationship('Box', back_populates='items')

    def __repr__(self) -> str:
        return f"""Book(
        id={self.id!r},
        isbn={self.isbn!r},
        title={self.title!r},
        tags={self.tags!r},
        goodreads_url={self.goodreads_url!r},
        priority={self.priority!r},
        purchase_date={self.purchase_date!r},
        purchase_price={self.purchase_price!r},
        sell_date={self.sell_date!r},
        sell_price={self.sell_price!r},
        read_start_date={self.read_start_date!r},
        read_finish_date={self.read_finish_date!r},
        rating={self.rating!r},
        abandoned={self.abandoned!r},
        location={self.location!r}
        notes={self.notes!r}
        )"""
