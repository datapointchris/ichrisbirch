import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data
from ichrisbirch import schemas
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('books')
    yield
    delete_test_data('books')


ENDPOINT = '/books/'
NEW_OBJ = schemas.BookCreate(
    isbn="9780743273565",
    title="The Great Gatsby",
    author="F. Scott Fitzgerald",
    tags=["Classic", "Fiction", "American Literature"],
    goodreads_url="https://www.goodreads.com/book/show/4671.The_Great_Gatsby",
    priority=4,
    rating=4,
    location="Bookshelf",
    notes="A classic American novel",
)
crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='title')


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in)


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in)


def test_search_book(test_api_logged_in):
    # Test searching by title
    search_term = 'hobbit'
    search_results = test_api_logged_in.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1
    
    # Test searching by author
    search_term = 'orwell'
    search_results = test_api_logged_in.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1
    
    # Test searching by tag
    search_term = 'fantasy'
    search_results = test_api_logged_in.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    assert len(search_results.json()) == 1
    
    # Test searching by multiple tags
    search_term = 'classic'
    search_results = test_api_logged_in.get('/books/search/', params={'q': search_term})
    assert search_results.status_code == status.HTTP_200_OK, show_status_and_response(search_results)
    # All 3 books have the "Classic" tag
    assert len(search_results.json()) == 3


def test_get_book_by_isbn(test_api_logged_in):
    # Test getting a book by ISBN that exists
    isbn = "9780451524935"  # 1984
    response = test_api_logged_in.get(f'/books/isbn/{isbn}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['title'] == "1984"
    
    # Test getting a book by ISBN that doesn't exist
    isbn = "9999999999999"
    response = test_api_logged_in.get(f'/books/isbn/{isbn}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is None


def test_update_book(test_api_logged_in):
    # Get the first book
    book_id = 1
    book = test_api_logged_in.get(f'/books/{book_id}/')
    assert book.status_code == status.HTTP_200_OK, show_status_and_response(book)
    
    # Update the book's rating
    update_data = {"rating": 3}
    updated = test_api_logged_in.patch(f'/books/{book_id}/', json=update_data)
    assert updated.status_code == status.HTTP_200_OK, show_status_and_response(updated)
    assert updated.json()['rating'] == 3
    
    # Update multiple fields
    update_data = {"notes": "Updated notes", "location": "Office"}
    updated = test_api_logged_in.patch(f'/books/{book_id}/', json=update_data)
    assert updated.status_code == status.HTTP_200_OK, show_status_and_response(updated)
    assert updated.json()['notes'] == "Updated notes"
    assert updated.json()['location'] == "Office"


@patch('httpx.get')
def test_goodreads_info(mock_get, test_api_logged_in):
    # Mock the httpx.get response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = mock_response
    mock_response.url = "https://www.goodreads.com/book/show/12345"
    
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
    response = test_api_logged_in.post('/books/goodreads/', json={"isbn": "9780743273565"})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    
    # Verify the response
    data = response.json()
    assert data['title'] == "The Great Gatsby"
    assert data['author'] == "F. Scott Fitzgerald"
    assert "Fiction, Classics" in data['tags']
    assert data['goodreads_url'] == "https://www.goodreads.com/book/show/12345"
    
    # Verify the mock was called with the expected URL
    mock_get.assert_called_once()