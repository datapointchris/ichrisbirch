from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator


class BookConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BookCreate(BookConfig):
    isbn: str
    title: str
    author: str
    tags: list[str]
    goodreads_url: str | None = None
    priority: int | None = None
    purchase_date: datetime | None = None
    purchase_price: float | None = None
    sell_date: datetime | None = None
    sell_price: float | None = None
    read_start_date: datetime | None = None
    read_finish_date: datetime | None = None
    rating: int | None = None
    abandoned: bool | None = None
    location: str | None = None
    notes: str | None = None

    @model_validator(mode='before')
    @classmethod
    def empty_field_to_none(cls, data):
        if isinstance(data, dict):
            return {k: (v or None) for k, v in data.items()}
        return data


class Book(BookConfig):
    id: int
    isbn: str
    title: str
    author: str
    tags: list[str]
    goodreads_url: str | None = None
    priority: int | None = None
    purchase_date: datetime | None = None
    purchase_price: float | None = None
    sell_date: datetime | None = None
    sell_price: float | None = None
    read_start_date: datetime | None = None
    read_finish_date: datetime | None = None
    rating: int | None = None
    abandoned: bool | None = None
    location: str | None = None
    notes: str | None = None


class BookUpdate(BookConfig):
    isbn: str | None = None
    title: str | None = None
    author: str | None = None
    tags: list[str] = []
    goodreads_url: str | None = None
    priority: int | None = None
    purchase_date: datetime | None = None
    purchase_price: float | None = None
    sell_date: datetime | None = None
    sell_price: float | None = None
    read_start_date: datetime | None = None
    read_finish_date: datetime | None = None
    rating: int | None = None
    abandoned: bool | None = None
    location: str | None = None
    notes: str | None = None


class BookGoodreadsInfo(BookConfig):
    title: str
    author: str
    tags: str
    goodreads_url: str
