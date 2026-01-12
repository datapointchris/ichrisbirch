from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/books/'
NEW_OBJ = schemas.BookCreate(
    isbn='9780743273565',
    title='The Great Gatsby',
    author='F. Scott Fitzgerald',
    tags=['Classic', 'Fiction', 'American Literature'],
    goodreads_url='https://www.goodreads.com/book/show/4671.The_Great_Gatsby',
    priority=4,
    rating=4,
    location='Bookshelf',
    notes='A classic American novel',
)


@pytest.fixture
def book_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'books')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='title')
    return client, crud_tester


def test_read_one(book_crud_tester):
    client, crud_tester = book_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(book_crud_tester):
    client, crud_tester = book_crud_tester
    crud_tester.test_read_many(client)


def test_create(book_crud_tester):
    client, crud_tester = book_crud_tester
    crud_tester.test_create(client)


def test_delete(book_crud_tester):
    client, crud_tester = book_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(book_crud_tester):
    client, crud_tester = book_crud_tester
    crud_tester.test_lifecycle(client)


def test_search_book(book_crud_tester):
    client, _ = book_crud_tester
    # Test searching by title
    search_term = 'hobbit'
    search_results = client.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    # Test searching by author
    search_term = 'orwell'
    search_results = client.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    # Test searching by tag
    search_term = 'fantasy'
    search_results = client.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1

    # Test searching by multiple tags
    search_term = 'classic'
    search_results = client.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    # All 3 books have the "Classic" tag
    assert len(search_results.json()) == 3


def test_get_book_by_isbn(book_crud_tester):
    client, _ = book_crud_tester
    # Test getting a book by ISBN that exists
    isbn = '9780451524935'  # 1984
    response = client.get(f'/books/isbn/{isbn}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['title'] == '1984'

    # Test getting a book by ISBN that doesn't exist returns 404
    isbn = '9999999999999'
    response = client.get(f'/books/isbn/{isbn}/')
    assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


def test_update_book(book_crud_tester):
    client, crud_tester = book_crud_tester
    # Get the first book dynamically
    book_id = crud_tester.item_id_by_position(client, position=1)
    book = client.get(f'/books/{book_id}/')
    assert book.status_code == status.HTTP_200_OK, show_status_and_response(book)

    # Update the book's rating
    update_data = {'rating': 3}
    updated = client.patch(f'/books/{book_id}/', json=update_data)
    assert updated.status_code == status.HTTP_200_OK, show_status_and_response(updated)
    assert updated.json()['rating'] == 3

    # Update multiple fields
    update_data = {'notes': 'Updated notes', 'location': 'Office'}
    updated = client.patch(f'/books/{book_id}/', json=update_data)
    assert updated.status_code == status.HTTP_200_OK, show_status_and_response(updated)
    assert updated.json()['notes'] == 'Updated notes'
    assert updated.json()['location'] == 'Office'


@patch('httpx.get')
def test_goodreads_info(mock_get, book_crud_tester):
    client, _ = book_crud_tester
    # Mock the httpx.get response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = mock_response
    mock_response.url = 'https://www.goodreads.com/book/show/12345'

    # Create mock HTML content with the expected structure
    mock_html = """
    <html>
        <body>
            <h1 class="Text Text__title1">The Great Gatsby</h1>
            <span class="ContributorLink__name">F. Scott Fitzgerald</span>
            <div class="BookPageMetadataSection__genres">
                <span class="Button__labelItem">Fiction</span>
                <span class="Button__labelItem">Classics</span>
                <span class="Button__labelItem">All Genres</span>
            </div>
        </body>
    </html>
    """
    mock_response.content = mock_html.encode('utf-8')
    mock_get.return_value = mock_response

    # Test the Goodreads endpoint
    response = client.post('/books/goodreads/', json={'isbn': '9780743273565'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    # Verify the response
    data = response.json()
    assert data['title'] == 'The Great Gatsby'
    assert data['author'] == 'F. Scott Fitzgerald'
    assert 'Fiction, Classics' in data['tags']
    assert data['goodreads_url'] == 'https://www.goodreads.com/book/show/12345'

    # Verify the mock was called with the expected URL
    mock_get.assert_called_once()
