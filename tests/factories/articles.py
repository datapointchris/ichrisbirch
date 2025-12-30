"""Article factory for generating test Article objects."""

from datetime import datetime

import factory

from ichrisbirch.models.article import Article

from .base import get_factory_session


class ArticleFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Article objects."""

    class Meta:
        model = Article
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    title = factory.Sequence(lambda n: f'Test Article {n + 1}')
    tags = factory.LazyFunction(lambda: ['test', 'article'])
    summary = factory.LazyAttribute(lambda obj: f'Summary of {obj.title}')
    url = factory.Sequence(lambda n: f'https://example.com/article/{n + 1}')
    save_date = factory.LazyFunction(datetime.now)
    last_read_date = None
    read_count = 0
    is_favorite = False
    is_current = True
    is_archived = False
    review_days = None
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.title}')

    class Params:
        # Usage: ArticleFactory(favorite=True)
        favorite = factory.Trait(is_favorite=True)
        # Usage: ArticleFactory(archived=True)
        archived = factory.Trait(is_archived=True, is_current=False)
        # Usage: ArticleFactory(read=True)
        read = factory.Trait(last_read_date=factory.LazyFunction(datetime.now), read_count=1)
        # Usage: ArticleFactory(heavily_read=True)
        heavily_read = factory.Trait(last_read_date=factory.LazyFunction(datetime.now), read_count=10, is_favorite=True)
