"""Tests for the books seeder."""

from __future__ import annotations

import pytest

from ichrisbirch.models.book import Book
from scripts.seed.seeders import books

pytestmark = [pytest.mark.seed, pytest.mark.integration]


class TestBookSeeder:
    def test_creates_books_for_all_ownership_types(self, db):
        books.clear(db)
        books.seed(db, scale=1)
        ownerships = {b.ownership for b in db.query(Book).all()}
        assert ownerships == {'owned', 'sold', 'donated', 'to_purchase', 'rejected'}

    def test_read_books_have_dates_and_rating(self, db):
        books.clear(db)
        books.seed(db, scale=1)
        read_books = db.query(Book).filter(Book.progress == 'read').all()
        assert len(read_books) >= 1
        for book in read_books:
            assert book.read_start_date is not None
            assert book.read_finish_date is not None
            assert book.rating is not None

    def test_unread_books_have_no_read_dates(self, db):
        books.clear(db)
        books.seed(db, scale=1)
        unread = db.query(Book).filter(Book.progress == 'unread').all()
        assert len(unread) >= 1
        for book in unread:
            assert book.read_start_date is None
            assert book.read_finish_date is None

    def test_rejected_books_have_reason(self, db):
        books.clear(db)
        books.seed(db, scale=1)
        rejected = db.query(Book).filter(Book.ownership == 'rejected').all()
        assert len(rejected) >= 1
        for book in rejected:
            assert book.reject_reason is not None

    def test_scale_multiplier(self, db):
        books.clear(db)
        r1 = books.seed(db, scale=1)
        books.clear(db)
        r2 = books.seed(db, scale=2)
        assert r2.count > r1.count
