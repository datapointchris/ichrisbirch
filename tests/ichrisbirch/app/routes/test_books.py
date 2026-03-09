"""Tests for Flask books routes.

These tests verify that the Flask app routes properly authenticate with the API using user session authentication.
"""

import re
from html import unescape
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


def _extract_form_values(html: str) -> dict:
    """Extract form field values from rendered HTML, simulating what a browser sees.

    Parses <input> and <textarea> elements to get the pre-filled values,
    exactly as a browser would when the user loads the edit page.
    """
    values = {}
    # Match input fields: name="field" ... value="val" (in either order)
    for match in re.finditer(r'<input[^>]*>', html):
        tag = match.group(0)
        name_match = re.search(r'name="([^"]*)"', tag)
        if not name_match:
            continue
        name = name_match.group(1)
        # Skip hidden/submit fields
        if name == 'csrf_token':
            continue
        type_match = re.search(r'type="([^"]*)"', tag)
        field_type = type_match.group(1) if type_match else 'text'
        if field_type == 'hidden' and name != 'id':
            continue
        if field_type == 'submit':
            continue
        if field_type == 'checkbox':
            values[name] = 'y' if 'checked' in tag else None
            continue
        value_match = re.search(r'value="([^"]*)"', tag)
        values[name] = unescape(value_match.group(1)) if value_match else ''
    # Match textarea fields
    for match in re.finditer(r'<textarea[^>]*name="([^"]*)"[^>]*>(.*?)</textarea>', html, re.DOTALL):
        values[match.group(1)] = unescape(match.group(2).strip())
    return values


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/books/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


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


def test_edit_page(test_app_logged_in, test_api_logged_in):
    books = test_api_logged_in.get('/books/')
    first_id = books.json()[0]['id']
    response = test_app_logged_in.get(f'/books/edit/{first_id}/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert b'Editing:' in response.data


def test_book_edit_round_trip(test_app_logged_in, test_api_logged_in):
    """Full integration test: load edit page, submit, re-edit, verify everything persists.

    This simulates what a real browser does: load the edit page, get the pre-filled
    form values, modify some, submit, then load the edit page again and re-submit.
    This catches bugs like:
    - WTForms rendering Python list repr instead of comma-separated string (tag nesting)
    - HTML checkboxes not sending data when unchecked (abandoned can't be cleared)
    - Form field values being corrupted through the render→submit round-trip
    """
    books = test_api_logged_in.get('/books/')
    book = books.json()[0]
    book_id = book['id']
    original_tags = book['tags']

    # === Edit 1: Load edit page, change rating and mark as abandoned ===
    edit_page = test_app_logged_in.get(f'/books/edit/{book_id}/')
    assert edit_page.status_code == 200
    form_data = _extract_form_values(edit_page.data.decode())
    form_data['action'] = 'edit'
    form_data['rating'] = '8'
    form_data['abandoned'] = 'y'
    form_data['notes'] = 'Great book, but giving up for now'
    test_app_logged_in.post('/books/crud/', data=form_data, follow_redirects=True)

    result = test_api_logged_in.get(f'/books/{book_id}/').json()
    assert result['rating'] == 8
    assert result['abandoned'] is True
    assert result['notes'] == 'Great book, but giving up for now'
    assert result['tags'] == [t.lower() for t in original_tags], 'Tags should survive the round-trip unchanged'

    # === Edit 2: Load edit page again, uncheck abandoned, change tags ===
    edit_page = test_app_logged_in.get(f'/books/edit/{book_id}/')
    form_data = _extract_form_values(edit_page.data.decode())
    form_data['action'] = 'edit'
    form_data['tags'] = 'Updated Tag, Another Tag'
    del form_data['abandoned']  # unchecked checkbox — browser doesn't send it
    test_app_logged_in.post('/books/crud/', data=form_data, follow_redirects=True)

    result = test_api_logged_in.get(f'/books/{book_id}/').json()
    assert result['tags'] == ['updated tag', 'another tag']
    assert result['abandoned'] is not True, 'Unchecking abandoned should clear it'
    assert result['rating'] == 8, 'Previous changes should persist'

    # === Edit 3: Load edit page one more time, submit without changes ===
    # This catches any corruption that accumulates through round-trips
    edit_page = test_app_logged_in.get(f'/books/edit/{book_id}/')
    form_data = _extract_form_values(edit_page.data.decode())
    form_data['action'] = 'edit'
    if form_data.get('abandoned') is None:
        del form_data['abandoned']
    test_app_logged_in.post('/books/crud/', data=form_data, follow_redirects=True)

    final = test_api_logged_in.get(f'/books/{book_id}/').json()
    assert final['tags'] == ['updated tag', 'another tag'], 'Tags should not change on no-op edit'
    assert final['rating'] == 8
    assert final['notes'] == 'Great book, but giving up for now'
    assert final['title'] == book['title'], 'Untouched fields should be unchanged'


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
