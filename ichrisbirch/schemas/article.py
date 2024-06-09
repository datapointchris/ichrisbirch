from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ArticleConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ArticleCreate(ArticleConfig):
    title: str
    url: str
    tags: list[str]
    summary: str | None = None
    notes: str | None = None
    save_date: datetime
    read_count: int = 0
    is_favorite: bool = False
    is_current: bool = False
    is_archived: bool = False
    review_days: int | None = None


class Article(ArticleConfig):
    id: int
    title: str
    url: str
    tags: list[str]
    summary: str | None = None
    notes: str | None = None
    save_date: datetime
    last_read_date: datetime | None = None
    read_count: int
    is_favorite: bool
    is_current: bool
    is_archived: bool
    review_days: int | None = None


class ArticleUpdate(ArticleConfig):
    title: str | None = None
    tags: list[str] = []
    summary: str | None = None
    notes: str | None = None
    is_favorite: bool | None = None
    is_current: bool | None = None
    is_archived: bool | None = None
    last_read_date: datetime | None = None
    read_count: int | None = None
    review_days: int | None = None


class ArticleSummary(ArticleConfig):
    title: str
    summary: str
    tags: list[str]
