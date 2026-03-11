"""Tests for MCP server tools against the real test API.

These tests call MCP tool functions directly, with _client patched to route
through the FastAPI TestClient. This means every tool call goes through real
Pydantic validation, real SQLAlchemy persistence, and real API responses.
"""

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pytest

from ichrisbirch.mcp import server as mcp_server
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional


@pytest.fixture
def mcp_with_api_key(txn_api_logged_in):
    """Create a personal API key and configure MCP server to use it."""
    client, session = txn_api_logged_in

    response = client.post('/api-keys/', json={'name': 'MCP Test Key'})
    assert response.status_code == 201, show_status_and_response(response)
    api_key = response.json()['key']

    return client, session, api_key


@pytest.fixture
def mcp_tools(mcp_with_api_key):
    """Patch MCP _client so tool calls go through the test API.

    The TestClient IS an httpx.Client, so MCP tool functions work unchanged.
    We just wrap it in a context manager that doesn't close the TestClient.
    """
    client, session, api_key = mcp_with_api_key
    client.headers['Authorization'] = f'Bearer {api_key}'

    class _TestClientCM:
        def __enter__(self):
            return client

        def __exit__(self, *args):
            pass

    with patch.object(mcp_server, '_client', return_value=_TestClientCM()):
        yield client, session


def _mock_article_externals():
    """Context manager that mocks httpx.get and OpenAIAssistant for article creation."""
    mock_response = MagicMock()
    mock_response.content = b'<html><head><title>Test Article | Website</title></head><body><p>Test content about Python.</p></body></html>'
    mock_response.raise_for_status.return_value = mock_response

    mock_assistant = MagicMock()
    mock_assistant.generate.return_value = json.dumps(
        {
            'summary': 'A test article about Python programming.',
            'tags': ['python', 'testing'],
        }
    )

    httpx_patch = patch('ichrisbirch.api.endpoints.articles.httpx.get', return_value=mock_response)
    openai_patch = patch('ichrisbirch.api.endpoints.articles.OpenAIAssistant', return_value=mock_assistant)

    return httpx_patch, openai_patch


def test_api_key_authenticates_for_tasks(mcp_with_api_key):
    """Verify that a personal API key can authenticate API requests."""
    client, session, api_key = mcp_with_api_key
    insert_test_data_transactional(session, 'tasks')

    response = client.get('/tasks/todo/', headers={'Authorization': f'Bearer {api_key}'})
    assert response.status_code == 200, show_status_and_response(response)
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) > 0


def test_api_key_create_and_delete_task(mcp_with_api_key):
    """Test write operations with API key auth (create + delete round-trip)."""
    client, session, api_key = mcp_with_api_key
    headers = {'Authorization': f'Bearer {api_key}'}

    task_data = {'name': 'MCP Test Task', 'category': 'Computer', 'priority': 5, 'notes': 'Created via MCP test'}
    create_response = client.post('/tasks/', json=task_data, headers=headers)
    assert create_response.status_code == 201, show_status_and_response(create_response)
    task_id = create_response.json()['id']

    delete_response = client.delete(f'/tasks/{task_id}/', headers=headers)
    assert delete_response.status_code == 204, show_status_and_response(delete_response)


def test_revoked_key_rejected(mcp_with_api_key):
    """Verify that a revoked API key is rejected.

    Note: In test environment, get_current_user is overridden for the logged-in client,
    so this test verifies the revoke operation itself works (revoked_at is set).
    Real auth rejection is tested in the API key endpoint tests.
    """
    client, session, api_key = mcp_with_api_key

    keys_response = client.get('/api-keys/')
    key_id = keys_response.json()[0]['id']
    revoke_response = client.delete(f'/api-keys/{key_id}/')
    assert revoke_response.status_code == 204

    list_response = client.get('/api-keys/')
    revoked_key = next(k for k in list_response.json() if k['id'] == key_id)
    assert revoked_key['revoked_at'] is not None


# ---------------------------------------------------------------------------
# MCP Book tool integration tests
# ---------------------------------------------------------------------------


class TestMcpBookTools:
    """Integration tests for MCP book tools against the real API."""

    def test_create_book_with_tags(self, mcp_tools):
        """create_book with comma-separated tags creates a real book in the database."""
        client, session = mcp_tools
        result = json.loads(mcp_server.create_book(title='The Iliad', author='Homer', tags='Classic, Poetry, Ancient'))
        assert 'id' in result
        assert result['tags'] == ['Classic', 'Poetry', 'Ancient']
        assert result['isbn'] is None

    def test_create_book_with_isbn(self, mcp_tools):
        """create_book with isbn persists it correctly."""
        client, session = mcp_tools
        result = json.loads(
            mcp_server.create_book(
                title='The Odyssey',
                author='Homer',
                tags='Classic, Poetry',
                isbn='9780140449136',
                goodreads_url='https://www.goodreads.com/book/show/1381',
            )
        )
        assert result['isbn'] == '9780140449136'
        assert result['goodreads_url'] == 'https://www.goodreads.com/book/show/1381'

    def test_create_book_tags_strips_whitespace(self, mcp_tools):
        """Extra whitespace in tags is stripped."""
        client, session = mcp_tools
        result = json.loads(mcp_server.create_book(title='Test', author='Author', tags='  Fiction ,  Classic , Adventure  '))
        assert result['tags'] == ['Fiction', 'Classic', 'Adventure']

    def test_update_book_tags(self, mcp_tools):
        """update_book converts comma-separated tags and persists them."""
        client, session = mcp_tools
        created = json.loads(mcp_server.create_book(title='To Update', author='Author', tags='Original'))
        updated = json.loads(mcp_server.update_book(id=created['id'], tags='New, Tags'))
        assert updated['tags'] == ['New', 'Tags']

    def test_update_book_without_tags_preserves_existing(self, mcp_tools):
        """Updating title without tags leaves existing tags untouched."""
        client, session = mcp_tools
        created = json.loads(mcp_server.create_book(title='Original Title', author='Author', tags='Keep'))
        updated = json.loads(mcp_server.update_book(id=created['id'], title='New Title'))
        assert updated['title'] == 'New Title'
        assert updated['tags'] == ['Keep']


# ---------------------------------------------------------------------------
# MCP Article tool integration tests
# ---------------------------------------------------------------------------


class TestMcpArticleTools:
    """Integration tests for MCP article tools against the real API.

    create_article now calls POST /articles/create-from-url/ which auto-summarizes
    via OpenAI, so we mock the external httpx.get and OpenAIAssistant calls.
    """

    def test_create_article_from_url(self, mcp_tools):
        """create_article with a URL auto-summarizes and creates the article."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            result = json.loads(mcp_server.create_article(url='https://example.com/test'))
        assert 'id' in result
        assert result['title'] == 'Test Article'
        assert result['summary'] == 'A test article about Python programming.'
        assert result['tags'] == ['python', 'testing']
        assert result['save_date'] is not None

    def test_create_article_with_notes(self, mcp_tools):
        """create_article persists notes alongside the auto-summary."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            result = json.loads(mcp_server.create_article(url='https://example.com/noted', notes='Important'))
        assert result['notes'] == 'Important'

    def test_create_article_duplicate_url(self, mcp_tools):
        """Creating two articles with the same URL returns a 409 conflict."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            first = json.loads(mcp_server.create_article(url='https://example.com/dup'))
            assert 'id' in first
            second = json.loads(mcp_server.create_article(url='https://example.com/dup'))
            assert second['error'] == 409

    def test_update_article_tags(self, mcp_tools):
        """update_article converts comma-separated tags and persists them."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            created = json.loads(mcp_server.create_article(url='https://example.com/update'))
        updated = json.loads(mcp_server.update_article(id=created['id'], tags='new, tags'))
        assert updated['tags'] == ['new', 'tags']

    def test_update_article_without_tags_preserves_existing(self, mcp_tools):
        """Updating title without tags leaves existing tags untouched."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            created = json.loads(mcp_server.create_article(url='https://example.com/keep'))
        updated = json.loads(mcp_server.update_article(id=created['id'], title='New Title'))
        assert updated['title'] == 'New Title'
        assert updated['tags'] == ['python', 'testing']

    def test_create_and_list_articles(self, mcp_tools):
        """Round-trip: create an article, then list should include it."""
        httpx_patch, openai_patch = _mock_article_externals()
        with httpx_patch, openai_patch:
            mcp_server.create_article(url='https://example.com/listed')
        articles = json.loads(mcp_server.list_articles())
        titles = [a['title'] for a in articles]
        assert 'Test Article' in titles


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestJsonResponseHelper:
    """Test the _json_response helper with real httpx.Response objects."""

    def test_success_response(self):
        response = httpx.Response(200, json=[{'id': 1, 'name': 'Test'}])
        result = json.loads(mcp_server._json_response(response))
        assert result == [{'id': 1, 'name': 'Test'}]

    def test_204_response(self):
        response = httpx.Response(204)
        result = json.loads(mcp_server._json_response(response))
        assert result == {'status': 'success'}

    def test_error_response(self):
        response = httpx.Response(401, text='Unauthorized')
        result = json.loads(mcp_server._json_response(response))
        assert result['error'] == 401
        assert 'Unauthorized' in result['detail']
