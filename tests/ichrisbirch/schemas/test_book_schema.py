"""Tests for the book schema validation.

Tests that BookCreate, Book, and BookUpdate schemas properly validate data,
especially around optional ISBN and required tags.
"""

import pytest
from pydantic import ValidationError

from ichrisbirch.schemas.book import Book
from ichrisbirch.schemas.book import BookCreate
from ichrisbirch.schemas.book import BookUpdate


class TestBookCreateSchema:
    def test_create_with_all_fields(self):
        """Test creating a BookCreate with all fields populated."""
        book = BookCreate(
            isbn='9780451524935',
            title='1984',
            author='George Orwell',
            tags=['Dystopian', 'Classic'],
            priority=1,
            rating=5,
        )
        assert book.isbn == '9780451524935'
        assert book.title == '1984'
        assert book.tags == ['Dystopian', 'Classic']

    def test_create_without_isbn(self):
        """ISBN should be optional — many books (pre-1970, special editions) lack ISBNs."""
        book = BookCreate(
            title='The Iliad',
            author='Homer',
            tags=['Classic', 'Poetry'],
        )
        assert book.isbn is None
        assert book.title == 'The Iliad'

    def test_create_with_explicit_none_isbn(self):
        """Explicitly passing isbn=None should work."""
        book = BookCreate(
            isbn=None,
            title='Beowulf',
            author='Unknown',
            tags=['Classic'],
        )
        assert book.isbn is None

    def test_create_with_empty_string_isbn_becomes_none(self):
        """The empty_field_to_none validator should convert '' to None for isbn."""
        book = BookCreate(
            isbn='',
            title='The Canterbury Tales',
            author='Geoffrey Chaucer',
            tags=['Classic'],
        )
        assert book.isbn is None

    def test_create_requires_tags(self):
        """Tags field is required — omitting it should raise ValidationError."""
        with pytest.raises(ValidationError):
            BookCreate(
                title='No Tags',
                author='Test Author',
            )

    def test_create_rejects_empty_tags(self):
        """An empty tags list should be rejected — at least one tag is required."""
        with pytest.raises(ValidationError, match='at least one tag is required'):
            BookCreate(
                title='Empty Tags',
                author='Test Author',
                tags=[],
            )

    def test_create_requires_title(self):
        """Title is required."""
        with pytest.raises(ValidationError):
            BookCreate(
                author='Test Author',
                tags=['Fiction'],
            )

    def test_create_requires_author(self):
        """Author is required."""
        with pytest.raises(ValidationError):
            BookCreate(
                title='Test Book',
                tags=['Fiction'],
            )

    def test_create_review_defaults_to_none(self):
        """Review should be optional and default to None."""
        book = BookCreate(
            title='Test Book',
            author='Test Author',
            tags=['Fiction'],
        )
        assert book.review is None

    def test_create_with_review(self):
        """Review can be set to a string value."""
        book = BookCreate(
            title='Test Book',
            author='Test Author',
            tags=['Fiction'],
            review='A compelling read',
        )
        assert book.review == 'A compelling read'


class TestBookSchema:
    def test_book_with_none_isbn(self):
        """The Book response schema should accept None isbn."""
        book = Book(
            id=1,
            title='The Iliad',
            author='Homer',
            tags=['Classic'],
            isbn=None,
        )
        assert book.isbn is None
        assert book.id == 1

    def test_book_without_isbn_field(self):
        """ISBN should default to None when not provided."""
        book = Book(
            id=1,
            title='The Iliad',
            author='Homer',
            tags=['Classic'],
        )
        assert book.isbn is None

    def test_book_with_isbn(self):
        """Normal case: book with ISBN."""
        book = Book(
            id=1,
            isbn='9780451524935',
            title='1984',
            author='George Orwell',
            tags=['Dystopian'],
        )
        assert book.isbn == '9780451524935'


class TestBookUpdateSchema:
    def test_update_isbn_already_optional(self):
        """BookUpdate.isbn was already optional — verify it still works."""
        update = BookUpdate(isbn=None)
        assert update.isbn is None

    def test_update_with_empty_string_isbn_becomes_none(self):
        """Empty string ISBN should be converted to None by the validator."""
        update = BookUpdate(isbn='')
        assert update.isbn is None

    def test_update_with_tags(self):
        """Tags can be updated."""
        update = BookUpdate(tags=['New Tag', 'Another Tag'])
        assert update.tags == ['New Tag', 'Another Tag']

    def test_update_review(self):
        """Review can be set in an update."""
        update = BookUpdate(review='Great book')
        assert update.review == 'Great book'

    def test_update_empty_review_becomes_none(self):
        """Empty string review should be converted to None by the validator."""
        update = BookUpdate(review='')
        assert update.review is None
