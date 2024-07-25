from datetime import datetime

from ichrisbirch.models import Article

BASE_DATA: list[Article] = [
    Article(
        title='Article 1',
        url='http://example.com/article1',
        tags=['1', 'one'],
        summary='Article 1 summary',
        is_current=True,
        is_favorite=False,
        is_archived=False,
        save_date=datetime(2023, 1, 1, 12, 0, 0),
        read_count=0,
        review_days=30,
    ),
    Article(
        title='Article 2',
        url='http://example.com/article2',
        tags=['2', 'two'],
        summary='Article 2 summary',
        is_current=False,
        is_favorite=True,
        is_archived=False,
        save_date=datetime(2023, 2, 1, 12, 0, 0),
        read_count=0,
    ),
    Article(
        title='Article 3',
        url='http://example.com/article3',
        tags=['3', 'three'],
        summary='Article 3 summary',
        is_current=False,
        is_favorite=False,
        is_archived=True,
        save_date=datetime(2023, 3, 1, 12, 0, 0),
        read_count=0,
    ),
]
