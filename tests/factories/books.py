"""Book factory for generating test Book objects."""

from datetime import datetime

import factory

from ichrisbirch.models.book import Book

from .base import get_factory_session


class BookFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Book objects."""

    class Meta:
        model = Book
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    isbn = factory.Sequence(lambda n: f'978-0-{n:06d}-{n % 10}-{n % 10}')
    title = factory.Sequence(lambda n: f'Test Book {n + 1}')
    author = factory.Sequence(lambda n: f'Author {n + 1}')
    tags = factory.LazyFunction(lambda: ['fiction', 'test'])
    goodreads_url = factory.Sequence(lambda n: f'https://goodreads.com/book/{n + 1}')
    priority = factory.Sequence(lambda n: n + 1)
    purchase_date = None
    purchase_price = None
    sell_date = None
    sell_price = None
    read_start_date = None
    read_finish_date = None
    rating = None
    abandoned = False
    location = 'Shelf'
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.title}')

    class Params:
        # Usage: BookFactory(reading=True)
        reading = factory.Trait(read_start_date=factory.LazyFunction(datetime.now), read_finish_date=None)
        # Usage: BookFactory(finished=True)
        finished = factory.Trait(
            read_start_date=factory.LazyFunction(datetime.now), read_finish_date=factory.LazyFunction(datetime.now), rating=4
        )
        # Usage: BookFactory(abandoned_book=True)
        abandoned_book = factory.Trait(read_start_date=factory.LazyFunction(datetime.now), abandoned=True)
        # Usage: BookFactory(purchased=True)
        purchased = factory.Trait(purchase_date=factory.LazyFunction(datetime.now), purchase_price=15.99)
