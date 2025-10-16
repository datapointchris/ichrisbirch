from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.base import Base


class Article(Base):
    __tablename__ = 'articles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    tags: Mapped[list[str]] = mapped_column(postgresql.ARRAY(String), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=True)
    save_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_read_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    read_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    review_days: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"""Article(
            title={self.title!r},
            tags={self.tags!r},
            summary={self.summary!r},
            url={self.url!r},
            save_date={self.save_date!r},
            last_read_date={self.last_read_date!r},
            read_count={self.read_count!r},
            is_favorite={self.is_favorite!r},
            is_current={self.is_current!r},
            review_days={self.review_days!r},
            notes={self.notes!r}
            )"""
