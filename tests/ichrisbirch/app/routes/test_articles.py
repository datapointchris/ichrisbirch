"""Tests for Flask articles routes.

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
    insert_test_data('articles')
    yield
    delete_test_data('articles')


def test_index(test_app_logged_in):
    response = test_app_logged_in.get('/articles/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_all(test_app_logged_in):
    response = test_app_logged_in.get('/articles/all/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_add_page(test_app_logged_in):
    response = test_app_logged_in.get('/articles/add/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_search_page(test_app_logged_in):
    response = test_app_logged_in.get('/articles/search/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_search_post(test_app_logged_in):
    response = test_app_logged_in.post('/articles/search/', data={'search_text': 'one'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_insights_page(test_app_logged_in):
    response = test_app_logged_in.get('/articles/insights/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


@patch('ichrisbirch.app.routes.articles.logging_flask_session_client')
def test_insights_post_uses_session_auth(mock_session_client, test_app_logged_in):
    """Verify that insights POST uses user session authentication."""
    mock_response = MagicMock()
    mock_response.text = '<h1>Test Insights</h1>'

    mock_resource = MagicMock()
    mock_resource.post_action.return_value = mock_response

    mock_client = MagicMock()
    mock_client.resource.return_value = mock_resource
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_session_client.return_value = mock_client

    response = test_app_logged_in.post('/articles/insights/', data={'url': 'https://example.com/test'})
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify logging_flask_session_client was called (indicates user session auth is used)
    mock_session_client.assert_called()


@patch('ichrisbirch.app.routes.articles.logging_flask_session_client')
def test_summarize_proxy_uses_session_auth(mock_session_client, test_app_logged_in):
    """Verify that summarize-proxy endpoint uses user session authentication."""
    mock_result = MagicMock()
    mock_result.title = 'Test Article'
    mock_result.summary = 'Test summary'
    mock_result.tags = ['test', 'article']

    mock_resource = MagicMock()
    mock_resource.post.return_value = mock_result

    mock_client = MagicMock()
    mock_client.resource.return_value = mock_resource
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_session_client.return_value = mock_client

    response = test_app_logged_in.post(
        '/articles/summarize-proxy/', data='{"url": "https://example.com/test"}', content_type='application/json'
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)

    # Verify logging_flask_session_client was called (indicates user session auth is used)
    mock_session_client.assert_called()

    # Verify response contains expected data
    data = response.get_json()
    assert data['title'] == 'Test Article'
    assert data['summary'] == 'Test summary'
    assert data['tags'] == ['test', 'article']


def test_summarize_proxy_missing_url(test_app_logged_in):
    """Verify that summarize-proxy returns 400 when URL is missing."""
    response = test_app_logged_in.post('/articles/summarize-proxy/', data='{}', content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_crud_add(test_app_logged_in):
    response = test_app_logged_in.post(
        '/articles/crud/',
        data=dict(
            title='New Test Article',
            url='http://example.com/new-article',
            tags='test, new',
            summary='New article summary',
            notes='',
            action='add',
        ),
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_archive(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 1, 'action': 'archive'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_unarchive(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 3, 'action': 'unarchive'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_make_favorite(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 1, 'action': 'make_favorite'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_unfavorite(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 2, 'action': 'unfavorite'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_make_current(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 2, 'action': 'make_current'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_remove_current(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 1, 'action': 'remove_current'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_mark_read(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 1, 'action': 'mark_read'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)


def test_crud_delete(test_app_logged_in):
    response = test_app_logged_in.post('/articles/crud/', data={'id': 1, 'action': 'delete'}, follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
