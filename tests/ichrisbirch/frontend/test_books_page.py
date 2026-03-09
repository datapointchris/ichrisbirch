import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.factories import BookFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_books(insert_users_for_login):
    """Create test books using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        BookFactory(
            title='1984',
            author='George Orwell',
            tags=['dystopian', 'classic', 'political'],
            rating=5,
            location='Bookshelf',
            notes='A classic dystopian novel',
        )
        BookFactory(
            title='The Hobbit',
            author='J.R.R. Tolkien',
            tags=['fantasy', 'adventure'],
            rating=None,
            abandoned=False,
        )
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.Book))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_books, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/books/')


def _get_book_from_db(title: str) -> models.Book:
    """Find a book by title via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Book).where(models.Book.title == title)).scalar_one()


def _get_book_by_id_from_db(book_id: int) -> models.Book:
    """Get a book by ID via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Book).where(models.Book.id == book_id)).scalar_one()


def test_books_index(page: Page):
    expect(page).to_have_title('Books')


def test_book_edit_round_trip(page: Page):
    """Full browser round-trip: edit a book, verify in DB, re-edit, verify stability.

    This catches the three bugs that originally motivated this test approach:
    1. Tag nesting: WTForms rendering tags as Python list repr "['dystopian', 'classic']"
       instead of "dystopian, classic" — causing tags to nest on each edit.
    2. Abandoned checkbox: Unchecking a checkbox means the browser doesn't send the field.
       If the backend doesn't handle this, abandoned can never be cleared.
    3. Data corruption through render→submit cycles: fields silently changing type or value
       when the form is loaded and re-submitted without user changes.
    """
    book = _get_book_from_db('1984')
    book_id = book.id

    # === Navigate to the edit page ===
    page.goto(f'{FRONTEND_BASE_URL}/books/edit/{book_id}/')
    expect(page).to_have_title('Edit Book')

    # Verify the tags field shows comma-separated text, NOT Python list repr.
    # This is the exact bug: WTForms would render ['dystopian', 'classic', 'political']
    # as the string "['dystopian', 'classic', 'political']" in the input field.
    tags_field = page.locator('input[name="tags"]')
    tags_value = tags_field.input_value()
    assert '[' not in tags_value, f'Tags should be comma-separated, not Python list repr: {tags_value}'
    assert 'dystopian' in tags_value

    # === Edit 1: Change rating, check abandoned, add notes ===
    page.locator('input[name="rating"]').fill('8')
    page.locator('input[name="abandoned"]').check()
    page.locator('textarea[name="notes"]').fill('Giving up for now')
    page.locator('button[value="edit"]').click()

    # Verify in DB that all changes persisted
    result = _get_book_by_id_from_db(book_id)
    assert result.rating == 8
    assert result.abandoned is True
    assert result.notes == 'Giving up for now'
    assert result.tags == ['dystopian', 'classic', 'political'], 'Tags should survive edit unchanged'

    # === Edit 2: Uncheck abandoned, change tags ===
    page.goto(f'{FRONTEND_BASE_URL}/books/edit/{book_id}/')
    expect(page).to_have_title('Edit Book')

    # Verify previous changes are shown in the form
    assert page.locator('input[name="rating"]').input_value() == '8'
    expect(page.locator('input[name="abandoned"]')).to_be_checked()

    # Verify tags are STILL comma-separated after the round-trip (not nested)
    tags_value = page.locator('input[name="tags"]').input_value()
    assert '[' not in tags_value, f'Tags got nested through round-trip: {tags_value}'

    # Uncheck abandoned and change tags
    page.locator('input[name="abandoned"]').uncheck()
    page.locator('input[name="tags"]').fill('updated tag, another tag')
    page.locator('button[value="edit"]').click()

    result = _get_book_by_id_from_db(book_id)
    assert result.tags == ['updated tag', 'another tag']
    assert result.abandoned is not True, 'Unchecking abandoned should clear it'
    assert result.rating == 8, 'Rating from previous edit should persist'

    # === Edit 3: No-op — load and submit without changes ===
    # This catches corruption that accumulates through render→submit cycles
    page.goto(f'{FRONTEND_BASE_URL}/books/edit/{book_id}/')

    # Verify tags haven't been corrupted
    tags_value = page.locator('input[name="tags"]').input_value()
    assert tags_value == 'updated tag, another tag', f'Tags corrupted before no-op submit: {tags_value}'

    page.locator('button[value="edit"]').click()

    final = _get_book_by_id_from_db(book_id)
    assert final.tags == ['updated tag', 'another tag'], 'No-op edit should not corrupt tags'
    assert final.rating == 8
    assert final.notes == 'Giving up for now'
    assert final.title == '1984', 'Untouched fields should be unchanged'
