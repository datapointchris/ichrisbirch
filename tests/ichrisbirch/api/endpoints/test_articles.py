import json
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.ArticleCreate(
    title='How to Use AI Agents',
    url='http://aiagents.com',
    tags=['ai agents', 'rag'],
    summary='AI agents are the future of computing.',
    save_date=datetime.now(),
)

ENDPOINT = '/articles/'


@pytest.fixture
def article_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'articles')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='title')
    return client, crud_tester


def test_read_one(article_crud_tester):
    client, crud_tester = article_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(article_crud_tester):
    client, crud_tester = article_crud_tester
    crud_tester.test_read_many(client)


def test_create(article_crud_tester):
    client, crud_tester = article_crud_tester
    crud_tester.test_create(client)


def test_delete(article_crud_tester):
    client, crud_tester = article_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(article_crud_tester):
    client, crud_tester = article_crud_tester
    crud_tester.test_lifecycle(client)


def test_read_current(article_crud_tester):
    client, _ = article_crud_tester
    response = client.get(f'{ENDPOINT}current/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is not None


def test_read_one_url(article_crud_tester):
    client, _ = article_crud_tester
    response = client.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    response = client.get(f'{ENDPOINT}url/', params={'url': NEW_OBJ.url})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    article = response.json()
    assert article is not None
    assert article['title'] == NEW_OBJ.title


def test_search(article_crud_tester):
    client, _ = article_crud_tester
    searchable_article = schemas.ArticleCreate(
        title='Searchable Article',
        url='http://search-test.com',
        tags=['test-search', 'findable'],
        summary='This article should be found by search',
        save_date=datetime.now(),
    )
    response = client.post(ENDPOINT, json=searchable_article.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    response = client.get(f'{ENDPOINT}search/', params={'q': 'test-search'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    articles = response.json()
    assert len(articles) > 0
    assert any(article['title'] == 'Searchable Article' for article in articles)


@patch('ichrisbirch.api.endpoints.articles.httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi')
@patch('youtube_transcript_api.formatters.TextFormatter')
def test_summarize(mock_text_formatter, mock_yt_api, mock_httpx_get, article_crud_tester):
    client, _ = article_crud_tester
    # Mock httpx.get response
    mock_response = MagicMock()
    mock_response.content = '<html><head><title>Test Article | Website</title></head><body><p>Test content</p></body></html>'
    mock_response.raise_for_status.return_value = mock_response
    mock_httpx_get.return_value = mock_response

    # Mock YouTube formatter (not used for non-YouTube URLs)
    mock_formatter = MagicMock()
    mock_formatter.format_transcript.return_value = 'Test transcript text'
    mock_text_formatter.return_value = mock_formatter

    # Mock OpenAIAssistant
    with patch('ichrisbirch.ai.assistants.openai.OpenAIAssistant') as mock_assistant_class:
        mock_assistant = MagicMock()
        mock_assistant_class.return_value = mock_assistant
        expected_summary = 'Test summary'
        expected_tags = ['test', 'article']
        mock_assistant.generate.return_value = json.dumps({'summary': expected_summary, 'tags': expected_tags})

        with patch('ichrisbirch.api.endpoints.articles.OpenAIAssistant', return_value=mock_assistant):
            response = client.post(f'{ENDPOINT}summarize/', json={'url': 'https://ichrisbirch.com/test-article'})
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
            data = response.json()
            assert data['title'] == 'Test Article'
            assert data['summary'] == expected_summary
            assert all(tag in data['tags'] for tag in expected_tags)


@patch('ichrisbirch.api.endpoints.articles.httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
def test_insights(mock_youtube_transcript_fetch, mock_httpx_get, article_crud_tester):
    client, _ = article_crud_tester
    # Mock httpx.get response
    mock_response = MagicMock()
    mock_response.content = '<html><head><title>Test Article | Website</title></head><body><p>Test content</p></body></html>'
    mock_response.raise_for_status.return_value = mock_response
    mock_httpx_get.return_value = mock_response

    # Mock YouTube transcript
    mock_youtube_transcript_fetch.return_value = [{'text': 'Test transcript', 'duration': 10}]

    # Mock OpenAIAssistant
    with patch('ichrisbirch.ai.assistants.openai.OpenAIAssistant') as mock_assistant_class:
        mock_assistant = MagicMock()
        mock_assistant.generate.return_value = '## Insights\n\nThis is a test insight.'
        mock_assistant_class.return_value = mock_assistant

        with patch('ichrisbirch.api.endpoints.articles.OpenAIAssistant', return_value=mock_assistant):
            response = client.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
            content = response.content.decode('utf-8')
            assert '<h1>Test Article</h1>' in content
            assert '<h2>Insights</h2>' in content


def test_archive(article_crud_tester):
    client, crud_tester = article_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'is_archived': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_unarchive(article_crud_tester):
    client, crud_tester = article_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'is_archived': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_favorite(article_crud_tester):
    client, crud_tester = article_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'is_favorite': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_unfavorite(article_crud_tester):
    client, crud_tester = article_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    response = client.patch(f'{ENDPOINT}{first_id}/', json={'is_favorite': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read(article_crud_tester):
    client, crud_tester = article_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    article = client.get(f'{ENDPOINT}{first_id}/').json()
    response = client.patch(
        f'{ENDPOINT}{first_id}/',
        json={
            'is_current': False,
            'is_archived': True,
            'last_read_date': str(datetime.now()),
            'read_count': article.get('read_count') + 1,
        },
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


class TestArticleQueryParameters:
    """Test query parameter filtering on /articles/ endpoint.

    Test data (from tests/test_data/articles.py):
    - Article 1: is_favorite=False, is_archived=False, last_read_date=None
    - Article 2: is_favorite=True, is_archived=False, last_read_date=None
    - Article 3: is_favorite=False, is_archived=True, last_read_date=None
    """

    def test_filter_archived_true(self, article_crud_tester):
        """archived=True returns only archived articles."""
        client, _ = article_crud_tester
        response = client.get(ENDPOINT, params={'archived': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 1
        assert articles[0]['is_archived'] is True
        assert articles[0]['title'] == 'Article 3'

    def test_filter_archived_false(self, article_crud_tester):
        """archived=False returns only non-archived articles."""
        client, _ = article_crud_tester
        response = client.get(ENDPOINT, params={'archived': False})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 2
        assert all(not a['is_archived'] for a in articles)

    def test_filter_unread_true(self, article_crud_tester):
        """unread=True returns articles with NULL last_read_date."""
        client, _ = article_crud_tester
        response = client.get(ENDPOINT, params={'unread': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        # All 3 test articles have last_read_date=None
        assert len(articles) == 3
        assert all(a['last_read_date'] is None for a in articles)

    def test_filter_unread_false(self, article_crud_tester):
        """unread=False returns articles that HAVE been read."""
        client, crud_tester = article_crud_tester
        # First mark one article as read
        first_id = crud_tester.item_id_by_position(client, position=1)
        client.patch(f'{ENDPOINT}{first_id}/', json={'last_read_date': str(datetime.now())})

        response = client.get(ENDPOINT, params={'unread': False})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 1
        assert all(a['last_read_date'] is not None for a in articles)

    def test_filter_favorites_false(self, article_crud_tester):
        """favorites=False returns only non-favorite articles."""
        client, _ = article_crud_tester
        response = client.get(ENDPOINT, params={'favorites': False})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 2  # Articles 1 and 3 are not favorites
        assert all(not a['is_favorite'] for a in articles)

    def test_filter_favorites_true_returns_unread_favorites(self, article_crud_tester):
        """favorites=True returns favorite articles that haven't been read yet."""
        client, _ = article_crud_tester
        # Article 2 is favorite and unread
        response = client.get(ENDPOINT, params={'favorites': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 1
        assert articles[0]['is_favorite'] is True
        assert articles[0]['title'] == 'Article 2'

    def test_filter_favorites_true_excludes_recently_read(self, article_crud_tester):
        """favorites=True excludes favorites that were recently read (not due for review)."""
        client, crud_tester = article_crud_tester
        # Get the favorite article (Article 2) and mark it as recently read
        response = client.get(ENDPOINT, params={'favorites': True})
        favorite_article = response.json()[0]

        # Mark as read with review_days set
        client.patch(
            f'{ENDPOINT}{favorite_article["id"]}/',
            json={'last_read_date': str(datetime.now()), 'review_days': 30},
        )

        # Now favorites=True should return empty (recently read, not due for review)
        response = client.get(ENDPOINT, params={'favorites': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 0

    def test_combined_filters(self, article_crud_tester):
        """Multiple filters can be combined."""
        client, _ = article_crud_tester
        # unread=True AND archived=False should return Articles 1 and 2
        response = client.get(ENDPOINT, params={'unread': True, 'archived': False})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 2
        assert all(a['last_read_date'] is None for a in articles)
        assert all(not a['is_archived'] for a in articles)

    def test_no_filters_returns_all(self, article_crud_tester):
        """No query parameters returns all articles."""
        client, _ = article_crud_tester
        response = client.get(ENDPOINT)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        articles = response.json()
        assert len(articles) == 3

    def test_url_not_found_returns_404(self, article_crud_tester):
        """Getting article by non-existent URL returns 404."""
        client, _ = article_crud_tester
        response = client.get(f'{ENDPOINT}url/', params={'url': 'http://nonexistent.com'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


def test_read_current_returns_null_when_no_articles(txn_api_logged_in):
    """Verify /current/ returns null (not error) when no articles exist."""
    client, _ = txn_api_logged_in
    response = client.get(f'{ENDPOINT}current/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is None


def test_read_many_returns_empty_list_when_no_articles(txn_api_logged_in):
    """Verify / returns empty list (not error) when no articles exist."""
    client, _ = txn_api_logged_in
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() == []
