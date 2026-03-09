"""Tests for Flask books routes.

These tests verify that the Flask app routes properly authenticate with the API using user session authentication.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import status

import tests.util
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('books')
    yield
    delete_test_data('books')


def test_add_page(test_app_logged_in):
    response = test_app_logged_in.get('/books/add/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


@patch('ichrisbirch.app.routes.books.logging_flask_session_client')
def test_goodreads_info_uses_session_auth(mock_session_client, test_app_logged_in):
    """Verify that goodreads-info endpoint uses user session authentication."""
    mock_result = MagicMock()
    mock_result.title = 'The Great Gatsby'
    mock_result.author = 'F. Scott Fitzgerald'
    mock_result.tags = 'Fiction, Classics'
    mock_result.goodreads_url = 'https://www.goodreads.com/book/show/4671'

    mock_resource = MagicMock()
    mock_resource.post.return_value = mock_result

    mock_client = MagicMock()
    mock_client.resource.return_value = mock_resource
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_session_client.return_value = mock_client

    response = test_app_logged_in.post('/books/goodreads-info/', data='{"isbn": "9780743273565"}', content_type='application/json')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify logging_flask_session_client was called (indicates user session auth is used)
    mock_session_client.assert_called()

    # Verify response contains expected data
    data = response.get_json()
    assert data['title'] == 'The Great Gatsby'
    assert data['author'] == 'F. Scott Fitzgerald'
    assert data['tags'] == 'Fiction, Classics'
    assert data['goodreads_url'] == 'https://www.goodreads.com/book/show/4671'


def test_goodreads_info_missing_isbn(test_app_logged_in):
    """Verify that goodreads-info returns 400 when ISBN is missing."""
    response = test_app_logged_in.post('/books/goodreads-info/', data='{}', content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_crud_add(test_app_logged_in):
    response = test_app_logged_in.post(
        '/books/crud/',
        data=dict(
            isbn='9780743273565',
            title='The Great Gatsby',
            author='F. Scott Fitzgerald',
            tags='Classic, Fiction, American Literature',
            goodreads_url='https://www.goodreads.com/book/show/4671',
            priority=4,
            action='add',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_add_duplicate(test_app_logged_in):
    """Verify that adding a book with an existing ISBN shows a warning."""
    response = test_app_logged_in.post(
        '/books/crud/',
        data=dict(
            isbn='9780451524935',
            title='1984',
            author='George Orwell',
            tags='Dystopian, Classic',
            action='add',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert b'already exists' in response.data


def test_crud_edit_with_empty_optional_fields(test_app_logged_in, test_api_logged_in):
    """Verify editing works when optional fields are submitted as empty strings (as HTML forms do)."""
    books = test_api_logged_in.get('/books/')
    book = books.json()[0]
    response = test_app_logged_in.post(
        '/books/crud/',
        data=dict(
            id=book['id'],
            isbn=book['isbn'],
            title='Updated Title',
            author=book['author'],
            tags='Classic',
            goodreads_url='',
            priority='',
            purchase_date='',
            purchase_price='',
            sell_date='',
            sell_price='',
            read_start_date='',
            read_finish_date='',
            rating='',
            location='',
            notes='',
            action='edit',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    updated = test_api_logged_in.get(f'/books/{book["id"]}/')
    assert updated.json()['title'] == 'Updated Title'


def test_crud_delete(test_app_logged_in, test_api_logged_in):
    books = test_api_logged_in.get('/books/')
    first_id = books.json()[0]['id']
    response = test_app_logged_in.post('/books/crud/', data={'id': first_id, 'action': 'delete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
