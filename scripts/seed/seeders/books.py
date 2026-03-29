"""Seed books with explicit ownership/progress combinations.

Instead of generating all 20 combos and fixing them up, we define the
valid combinations we actually want — constraints are visible in the
data instead of buried in conditional logic.
"""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.book import Book
from scripts.seed.base import SeedResult

TITLES = [
    'Designing Data-Intensive Applications',
    'The Art of PostgreSQL',
    'Atomic Habits',
    'The Pragmatic Programmer',
    'Deep Work',
    'Clean Code',
    'Project Hail Mary',
    'The DevOps Handbook',
    'Godel Escher Bach',
    'Introduction to Algorithms',
    'Fluent Python',
    'Staff Engineer',
    'Dune',
    'The Phoenix Project',
    'Database Internals',
    'Thinking Fast and Slow',
    'The Rust Programming Language',
    'Sapiens',
]

AUTHORS = [
    'Martin Kleppmann',
    'Dimitri Fontaine',
    'James Clear',
    'David Thomas and Andrew Hunt',
    'Cal Newport',
    'Robert C. Martin',
    'Andy Weir',
    'Gene Kim',
    'Douglas Hofstadter',
    'Thomas Cormen',
    'Luciano Ramalho',
    'Will Larson',
    'Frank Herbert',
    'Alex Petrov',
    'Daniel Kahneman',
    'Steve Klabnik',
    'Yuval Noah Harari',
]

TAGS = [
    ['programming', 'databases', 'distributed-systems'],
    ['databases', 'postgresql', 'sql'],
    ['productivity', 'self-help', 'habits'],
    ['programming', 'software-engineering'],
    ['productivity', 'focus'],
    ['programming', 'code-quality'],
    ['fiction', 'science-fiction'],
    ['devops', 'operations', 'software-engineering'],
    ['mathematics', 'philosophy', 'computer-science'],
    ['algorithms', 'computer-science', 'textbook'],
    ['python', 'programming'],
    ['career', 'engineering-leadership'],
    ['fiction', 'science-fiction', 'classic'],
    ['devops', 'fiction', 'business'],
    ['databases', 'internals', 'programming'],
    ['psychology', 'behavioral-economics'],
    ['rust', 'programming', 'systems'],
    ['history', 'anthropology', 'non-fiction'],
]

LOCATIONS = [
    'Living room bookshelf',
    'Office shelf',
    'Nightstand',
    'Storage box',
    'Kindle',
]

REJECT_REASONS = [
    "Superseded by author's later work",
    'Reviews indicate shallow treatment of the topic',
    'Too introductory for current knowledge level',
    'Available as blog posts by the same author',
    'Outdated edition, no modern revision available',
]

# (ownership, progress, has_read_dates, has_rating, has_purchase, has_reject)
BOOK_STATES = [
    ('owned', 'unread', False, False, True, False),
    ('owned', 'reading', True, False, True, False),
    ('owned', 'read', True, True, True, False),
    ('owned', 'read', True, True, True, False),
    ('owned', 'abandoned', True, False, True, False),
    ('sold', 'read', True, True, True, False),
    ('donated', 'read', True, True, True, False),
    ('donated', 'unread', False, False, True, False),
    ('to_purchase', 'unread', False, False, False, False),
    ('to_purchase', 'unread', False, False, False, False),
    ('rejected', 'unread', False, False, False, True),
    ('rejected', 'unread', False, False, False, True),
]


def _random_past_dt(days_back: int = 365) -> datetime:
    return datetime.now(UTC) - timedelta(days=random.randint(1, days_back))


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM books'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    books = []

    for rep in range(scale):
        for i, (ownership, progress, has_read, has_rating, has_purchase, has_reject) in enumerate(BOOK_STATES):
            title_idx = (i + rep * len(BOOK_STATES)) % len(TITLES)
            author_idx = title_idx % len(AUTHORS)

            title = TITLES[title_idx]
            if scale > 1:
                title = f'{title} #{rep + 1}'

            read_start = _random_past_dt(730) if has_read else None
            read_finish = None
            if has_read and progress == 'read' and read_start is not None:
                read_finish = read_start + timedelta(days=random.randint(7, 90))

            purchase_date = _random_past_dt(1095) if has_purchase else None
            purchase_price = round(random.uniform(9.99, 49.99), 2) if has_purchase else None

            sell_date = None
            sell_price = None
            if ownership == 'sold':
                sell_date = _random_past_dt(180)
                sell_price = round(random.uniform(5.00, 30.00), 2)

            books.append(
                Book(
                    title=title,
                    author=AUTHORS[author_idx],
                    tags=TAGS[title_idx % len(TAGS)],
                    ownership=ownership,
                    progress=progress,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    sell_date=sell_date,
                    sell_price=sell_price,
                    read_start_date=read_start,
                    read_finish_date=read_finish,
                    rating=random.randint(1, 10) if has_rating else None,
                    location=random.choice(LOCATIONS) if ownership == 'owned' else None,
                    reject_reason=random.choice(REJECT_REASONS) if has_reject else None,
                    notes=f'Great {TAGS[title_idx % len(TAGS)][0]} book' if i % 4 == 0 else None,
                )
            )

    session.add_all(books)
    session.flush()

    by_ownership: dict[str, int] = {}
    for b in books:
        by_ownership[b.ownership] = by_ownership.get(b.ownership, 0) + 1
    ownership_summary = ', '.join(f'{v} {k}' for k, v in sorted(by_ownership.items()))

    return SeedResult(
        model='Book',
        count=len(books),
        details=ownership_summary,
    )
