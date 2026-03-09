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
    """Test multiple rounds of updates to a book, covering various field types.

    Exercises the real update flow: change fields, verify they persist, change more,
    verify previous changes weren't clobbered and new ones stuck.
    """
    client, crud_tester = book_crud_tester
    book_id = crud_tester.item_id_by_position(client, position=1)
    original = client.get(f'/books/{book_id}/').json()

    # Round 1: Update simple fields
    response = client.patch(f'/books/{book_id}/', json={'rating': 3, 'notes': 'Updated notes', 'location': 'Office'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    book = response.json()
    assert book['rating'] == 3
    assert book['notes'] == 'Updated notes'
    assert book['location'] == 'Office'
    assert book['tags'] == original['tags'], 'Tags should not change when not sent'

    # Round 2: Update tags and set abandoned
    response = client.patch(f'/books/{book_id}/', json={'tags': ['NewTag1', 'NewTag2'], 'abandoned': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    book = response.json()
    assert book['tags'] == ['NewTag1', 'NewTag2']
    assert book['abandoned'] is True
    assert book['rating'] == 3, 'Previous update should persist'
    assert book['notes'] == 'Updated notes', 'Previous update should persist'

    # Round 3: Clear abandoned by setting to False
    response = client.patch(f'/books/{book_id}/', json={'abandoned': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    book = response.json()
    assert book['abandoned'] is False, 'Should be able to explicitly set abandoned=False'
    assert book['tags'] == ['NewTag1', 'NewTag2'], 'Tags should not change when not sent'

    # Final verification: read fresh and check all accumulated changes
    final = client.get(f'/books/{book_id}/').json()
    assert final['rating'] == 3
    assert final['notes'] == 'Updated notes'
    assert final['location'] == 'Office'
    assert final['tags'] == ['NewTag1', 'NewTag2']
    assert final['abandoned'] is False
    assert final['title'] == original['title'], 'Untouched fields should be unchanged'


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


class TestBookWithoutISBN:
    """Test creating and managing books without ISBN."""

    def test_create_book_without_isbn(self, book_crud_tester):
        """Books without ISBN (e.g. pre-1970, Easton Press editions) should be creatable."""
        client, _ = book_crud_tester
        book_data = {
            'title': 'The Iliad',
            'author': 'Homer',
            'tags': ['Classic', 'Poetry', 'Ancient'],
            'notes': 'Pre-ISBN era book',
        }
        response = client.post(ENDPOINT, json=book_data)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        data = response.json()
        assert data['title'] == 'The Iliad'
        assert data['isbn'] is None
        assert data['tags'] == ['Classic', 'Poetry', 'Ancient']

    def test_create_book_with_explicit_null_isbn(self, book_crud_tester):
        """Explicitly passing isbn=None should work."""
        client, _ = book_crud_tester
        book_data = {
            'isbn': None,
            'title': 'Beowulf',
            'author': 'Unknown',
            'tags': ['Classic', 'Poetry'],
        }
        response = client.post(ENDPOINT, json=book_data)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['isbn'] is None

    def test_create_book_with_isbn_still_works(self, book_crud_tester):
        """Books with ISBN should continue to work as before."""
        client, _ = book_crud_tester
        book_data = {
            'isbn': '9780140449136',
            'title': 'The Odyssey',
            'author': 'Homer',
            'tags': ['Classic', 'Poetry'],
        }
        response = client.post(ENDPOINT, json=book_data)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['isbn'] == '9780140449136'

    def test_update_book_isbn_to_none(self, book_crud_tester):
        """Should be able to clear a book's ISBN."""
        client, crud_tester = book_crud_tester
        book_id = crud_tester.item_id_by_position(client, position=1)
        # Verify the book currently has an ISBN
        book = client.get(f'{ENDPOINT}{book_id}/')
        assert book.json()['isbn'] is not None

        # Clear the ISBN
        response = client.patch(f'{ENDPOINT}{book_id}/', json={'isbn': None})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['isbn'] is None


class TestBookTagsValidation:
    """Test tags validation — at least one tag is required."""

    def test_create_book_with_empty_tags_rejected(self, book_crud_tester):
        """Creating a book with empty tags list should fail validation."""
        client, _ = book_crud_tester
        book_data = {
            'title': 'No Tags Book',
            'author': 'Test Author',
            'tags': [],
        }
        response = client.post(ENDPOINT, json=book_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, show_status_and_response(response)

    def test_create_book_with_one_tag(self, book_crud_tester):
        """A single tag should be valid."""
        client, _ = book_crud_tester
        book_data = {
            'title': 'One Tag Book',
            'author': 'Test Author',
            'tags': ['Fiction'],
        }
        response = client.post(ENDPOINT, json=book_data)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['tags'] == ['Fiction']


class TestBooksNotFound:
    """Test 404 responses for non-existent books."""

    def test_read_one_not_found(self, book_crud_tester):
        """GET /{id}/ returns 404 for non-existent book."""
        client, _ = book_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, book_crud_tester):
        """DELETE /{id}/ returns 404 for non-existent book."""
        client, _ = book_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, book_crud_tester):
        """PATCH /{id}/ returns 404 for non-existent book."""
        client, _ = book_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'title': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
