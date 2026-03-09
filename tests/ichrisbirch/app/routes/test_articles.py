"""Tests for Flask articles routes that require mocking or test edge cases.

User-facing flows (add, status transitions, search, delete) are tested
via Playwright in tests/ichrisbirch/frontend/test_articles_page.py.
These tests cover things that need mocking (external API proxies) or
edge cases that are simpler to test server-side (empty state pages).
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

    mock_session_client.assert_called()

    data = response.get_json()
    assert data['title'] == 'Test Article'
    assert data['summary'] == 'Test summary'
    assert data['tags'] == ['test', 'article']


def test_summarize_proxy_missing_url(test_app_logged_in):
    """Verify that summarize-proxy returns 400 when URL is missing."""
    response = test_app_logged_in.post('/articles/summarize-proxy/', data='{}', content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_index_with_no_articles(test_app_logged_in):
    """Verify articles index page works when no articles exist."""
    delete_test_data('articles')

    response = test_app_logged_in.get('/articles/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert b'No articles' in response.data


def test_all_with_no_articles(test_app_logged_in):
    """Verify articles all page works when no articles exist."""
    delete_test_data('articles')

    response = test_app_logged_in.get('/articles/all/')
    assert response.status_code == status.HTTP_200_OK, tests.util.show_status_and_response(response)
    assert b'No Articles' in response.data
