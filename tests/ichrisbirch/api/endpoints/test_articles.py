import asyncio
import datetime as dt
import json
import time
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import redis
from fastapi import status

from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AssistantFailure
from ichrisbirch.ai.assistants.anthropic import AssistantOutputError
from ichrisbirch.ai.assistants.anthropic import AssistantUsageLimitReached
from ichrisbirch.api.article_import_worker import BATCH_KEY_PREFIX
from ichrisbirch.api.article_import_worker import BATCH_TTL
from ichrisbirch.api.article_import_worker import PAUSE_KEY
from ichrisbirch.api.article_import_worker import QUEUE_KEY
from ichrisbirch.api.article_import_worker import USAGE_LIMIT_RECHECK
from ichrisbirch.api.article_import_worker import ArticleImportWorker
from ichrisbirch.api.article_import_worker import enqueue_bulk_import
from ichrisbirch.config import get_settings
from ichrisbirch.services.outbound_http import PageFetchError
from ichrisbirch.services.outbound_http import PageStatusError
from ichrisbirch.services.url_extraction import ArticlePage
from ichrisbirch.services.url_extraction import CaptionsBlocked
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.ArticleCreate(
    title='How to Use AI Agents',
    url='http://aiagents.com',
    tags=['ai agents', 'rag'],
    summary='AI agents are the future of computing.',
    save_date=dt.datetime.now(dt.UTC),
)

ENDPOINT = '/articles/'

PAGE = ArticlePage(url='https://example.com/test-article', title='Test Article', text='Test content')


def _patched_assistant(mock_assistant):
    """Patch AnthropicAssistant in the articles module so every instance is `mock_assistant`."""
    return patch('ichrisbirch.api.endpoints.articles.AnthropicAssistant', MagicMock(return_value=mock_assistant))


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
        save_date=dt.datetime.now(dt.UTC),
    )
    response = client.post(ENDPOINT, json=searchable_article.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    response = client.get(f'{ENDPOINT}search/', params={'q': 'test-search'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    articles = response.json()
    assert len(articles) > 0
    assert any(article['title'] == 'Searchable Article' for article in articles)


@patch('ichrisbirch.api.endpoints.articles.read_article_page')
@patch('youtube_transcript_api.YouTubeTranscriptApi')
@patch('youtube_transcript_api.formatters.TextFormatter')
def test_summarize(mock_text_formatter, mock_yt_api, mock_get_page, article_crud_tester):
    client, _ = article_crud_tester
    # Mock the outbound page fetch
    mock_get_page.return_value = PAGE

    # Mock YouTube formatter (not used for non-YouTube URLs)
    mock_formatter = MagicMock()
    mock_formatter.format_transcript.return_value = 'Test transcript text'
    mock_text_formatter.return_value = mock_formatter

    mock_assistant = MagicMock()
    expected_summary = 'Test summary'
    expected_tags = ['test', 'article']
    mock_assistant.generate_structured = AsyncMock(return_value=schemas.ArticleSummaryAndTags(summary=expected_summary, tags=expected_tags))

    with _patched_assistant(mock_assistant):
        response = client.post(f'{ENDPOINT}summarize/', json={'url': 'https://ichrisbirch.com/test-article'})
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        data = response.json()
        assert data['title'] == 'Test Article'
        assert data['summary'] == expected_summary
        assert all(tag in data['tags'] for tag in expected_tags)


@patch('ichrisbirch.api.endpoints.articles.read_article_page')
@patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
def test_insights(mock_youtube_transcript_fetch, mock_get_page, article_crud_tester):
    client, _ = article_crud_tester
    # Mock the outbound page fetch
    mock_get_page.return_value = PAGE

    # Mock YouTube transcript
    mock_youtube_transcript_fetch.return_value = [{'text': 'Test transcript', 'duration': 10}]

    mock_assistant = MagicMock()
    mock_assistant.generate = AsyncMock(return_value='## Insights\n\nThis is a test insight.')

    with _patched_assistant(mock_assistant):
        response = client.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        content = response.content.decode('utf-8')
        assert '<h1>Test Article</h1>' in content
        assert '<h2>Insights</h2>' in content


@patch('ichrisbirch.api.endpoints.articles.read_article_page')
@patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
def test_insights_refuses_a_truncated_reply(mock_youtube_transcript_fetch, mock_get_page, article_crud_tester):
    """Insights renders the reply without parsing it, so truncation has no other tell.

    The prompt says there is no limit to the number or length of insights, and
    a reply stopped at the cap renders as finished HTML.
    """
    client, _ = article_crud_tester
    mock_get_page.return_value = PAGE
    mock_youtube_transcript_fetch.return_value = [{'text': 'Test transcript', 'duration': 10}]

    mock_assistant = MagicMock()
    mock_assistant.generate = AsyncMock(
        side_effect=AssistantOutputError(AssistantFailure.TRUNCATED, 'cap reached', '## Insights\n\nThe first one is that')
    )

    with _patched_assistant(mock_assistant):
        response = client.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})

    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY, show_status_and_response(response)
    assert response.json()['detail']['reason'] == AssistantFailure.TRUNCATED


@patch('ichrisbirch.api.endpoints.articles.read_article_page')
@patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
def test_insights_neutralizes_html_in_the_model_output(mock_youtube_transcript_fetch, mock_get_page, article_crud_tester):
    """The model summarizes a page the caller supplied, so its output is attacker-influenced.

    Both consumers render this response as HTML, so a <script> reaching the
    response would execute in the reader's browser.
    """
    client, _ = article_crud_tester
    mock_get_page.return_value = PAGE
    mock_youtube_transcript_fetch.return_value = [{'text': 'Test transcript', 'duration': 10}]

    mock_assistant = MagicMock()
    mock_assistant.generate = AsyncMock(return_value='## Insights\n\n<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>')

    with _patched_assistant(mock_assistant):
        response = client.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})

    content = response.content.decode('utf-8')
    # The angle brackets are what make a tag a tag. Escaped, the payload is
    # text the reader sees rather than markup the browser runs, so asserting on
    # the substring 'onerror=' would fail on inert content.
    assert '<script>' not in content, 'a script tag from the model reached the response'
    assert '<img' not in content, 'an img tag from the model reached the response'
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content, 'the tag should survive as visible text'
    assert '&lt;img src=x onerror=alert(1)&gt;' in content, 'the tag should survive as visible text'
    assert '<h2>Insights</h2>' in content, 'markdown formatting must still render'


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
            'last_read_date': str(dt.datetime.now(dt.UTC)),
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
        client.patch(f'{ENDPOINT}{first_id}/', json={'last_read_date': str(dt.datetime.now(dt.UTC))})

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
            json={'last_read_date': str(dt.datetime.now(dt.UTC)), 'review_days': 30},
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


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


def test_create_article_without_summary_returns_422(txn_api_logged_in):
    """POST /articles/ without summary returns 422 (summary is required)."""
    client, _ = txn_api_logged_in
    payload = {'title': 'No Summary', 'url': 'http://nosummary.com', 'save_date': str(dt.datetime.now(dt.UTC))}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


def test_create_article_without_save_date_returns_422(txn_api_logged_in):
    """POST /articles/ without save_date returns 422 (save_date is required)."""
    client, _ = txn_api_logged_in
    payload = {'title': 'No Date', 'url': 'http://nodate.com', 'summary': 'Some summary'}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


# ---------------------------------------------------------------------------
# create-from-url endpoint tests
# ---------------------------------------------------------------------------


class TestCreateFromUrl:
    """Tests for POST /articles/create-from-url/ endpoint."""

    def _mock_externals(self, generate_raises: Exception | None = None):
        """Return the page-fetch and assistant patch context managers."""
        mock_assistant = MagicMock()
        if generate_raises is not None:
            mock_assistant.generate_structured = AsyncMock(side_effect=generate_raises)
        else:
            written = schemas.ArticleSummaryAndTags(summary='A test summary.', tags=['python', 'testing'])
            mock_assistant.generate_structured = AsyncMock(return_value=written)

        get_page_patch = patch('ichrisbirch.api.endpoints.articles.read_article_page', return_value=PAGE)
        return get_page_patch, _patched_assistant(mock_assistant)

    def test_create_from_url(self, txn_api_logged_in):
        """Create article from URL: fetches, summarizes, persists."""
        client, _ = txn_api_logged_in
        get_page_patch, assistant_patch = self._mock_externals()
        with get_page_patch, assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/test'})
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        data = response.json()
        assert data['title'] == 'Test Article'
        assert data['summary'] == 'A test summary.'
        assert data['tags'] == ['python', 'testing']
        assert data['save_date'] is not None

    def test_create_from_url_duplicate_returns_409(self, txn_api_logged_in):
        """Duplicate URL returns 409 Conflict."""
        client, _ = txn_api_logged_in
        get_page_patch, assistant_patch = self._mock_externals()
        with get_page_patch, assistant_patch:
            response1 = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/dup'})
            assert response1.status_code == status.HTTP_201_CREATED
            response2 = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/dup'})
            assert response2.status_code == status.HTTP_409_CONFLICT

    def test_create_from_url_with_notes(self, txn_api_logged_in):
        """Notes are persisted alongside the auto-summary."""
        client, _ = txn_api_logged_in
        get_page_patch, assistant_patch = self._mock_externals()
        with get_page_patch, assistant_patch:
            response = client.post(
                f'{ENDPOINT}create-from-url/',
                json={'url': 'https://example.com/noted', 'notes': 'Read later'},
            )
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['notes'] == 'Read later'

    @pytest.mark.parametrize(
        'failure',
        [
            PageFetchError('https://example.com/dead', 'connection refused'),
            PageStatusError('https://example.com/dead', 403),
            CaptionsBlocked('https://www.youtube.com/watch?v=abc'),
        ],
        ids=['unreachable', 'refused', 'captions-blocked'],
    )
    def test_create_from_url_reports_a_failing_site_as_a_failed_dependency(self, txn_api_logged_in, failure):
        """The detail names what failed, which is what a caller needs to decide whether to retry."""
        client, _ = txn_api_logged_in
        _, assistant_patch = self._mock_externals()
        with patch('ichrisbirch.api.endpoints.articles.read_article_page', side_effect=failure), assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/dead'})
        assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY, show_status_and_response(response)
        assert response.json()['detail'] == str(failure)

    def test_create_from_url_reports_invalid_output_as_a_failed_dependency(self, txn_api_logged_in):
        """The raw output comes back, so prompt drift is diagnosable without the logs."""
        client, _ = txn_api_logged_in
        invalid = AssistantOutputError(
            AssistantFailure.INVALID_OUTPUT, 'not a valid ArticleSummaryAndTags', 'I could not summarize that page.'
        )
        get_page_patch, assistant_patch = self._mock_externals(generate_raises=invalid)
        with get_page_patch, assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/prose'})
        assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY, show_status_and_response(response)
        detail = response.json()['detail']
        assert detail['reason'] == AssistantFailure.INVALID_OUTPUT
        assert detail['raw_assistant_output'] == 'I could not summarize that page.'

    def test_create_from_url_reports_a_truncated_reply_as_a_failed_dependency(self, txn_api_logged_in):
        """A reply stopped at the cap is a fragment, and must not be saved as an article."""
        client, _ = txn_api_logged_in
        truncated = AssistantOutputError(AssistantFailure.TRUNCATED, 'cap reached', '{"summary": "half a sum')
        get_page_patch, assistant_patch = self._mock_externals(generate_raises=truncated)
        with get_page_patch, assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/truncated'})
        assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY, show_status_and_response(response)
        assert response.json()['detail']['reason'] == AssistantFailure.TRUNCATED

    def test_an_unusable_reply_gives_the_bulk_worker_a_short_message(self, txn_api_logged_in):
        """The worker records str(e) in a database column and a Redis payload.

        An HTTPException stringifies as '424: {…}', so raising one from the
        shared helper would put the model's whole reply in both.
        """
        from ichrisbirch.api.endpoints.articles import _summarize_and_create_article

        client, session = txn_api_logged_in
        long_reply = 'x' * 4000
        invalid = AssistantOutputError(AssistantFailure.INVALID_OUTPUT, 'not a valid ArticleSummaryAndTags', long_reply)
        get_page_patch, assistant_patch = self._mock_externals(generate_raises=invalid)
        with get_page_patch, assistant_patch, pytest.raises(AssistantOutputError) as caught:
            asyncio.run(_summarize_and_create_article('https://example.com/worker', None, session, get_settings()))
        assert len(str(caught.value)) < 200, 'the worker would record this whole string'
        assert caught.value.raw_output == long_reply, 'the raw reply is still reachable for a 424'

    def test_create_from_url_answers_a_usage_limit_with_when_to_retry(self, txn_api_logged_in):
        """A refused call succeeds once the plan resets, so the answer is a 503 that says when."""
        client, _ = txn_api_logged_in
        resets_at = dt.datetime(2026, 9, 18, 3, 0, tzinfo=dt.UTC)
        limit = AssistantUsageLimitReached('Article Summary with Tags', resets_at, 'five_hour')
        get_page_patch, assistant_patch = self._mock_externals(generate_raises=limit)
        with get_page_patch, assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/limited'})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, show_status_and_response(response)
        assert response.headers['Retry-After'] == 'Fri, 18 Sep 2026 03:00:00 GMT'

    def test_a_usage_limit_with_no_reset_time_sends_no_retry_after(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        limit = AssistantUsageLimitReached('Article Summary with Tags', None, None)
        get_page_patch, assistant_patch = self._mock_externals(generate_raises=limit)
        with get_page_patch, assistant_patch:
            response = client.post(f'{ENDPOINT}create-from-url/', json={'url': 'https://example.com/limited'})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, show_status_and_response(response)
        assert 'Retry-After' not in response.headers


# ---------------------------------------------------------------------------
# Bulk import endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def test_redis():
    """Connect to test Redis on port 6380 db=1, isolated from container worker on db=0."""
    client = redis.Redis(host='localhost', port=6380, db=1, decode_responses=True)
    yield client
    # Cleanup: delete all article_import keys
    for key in client.keys('article_import:*'):
        client.delete(key)
    client.close()


@pytest.fixture
def api_with_redis(txn_api_logged_in, test_redis):
    """API client with Redis on db=1, isolated from the container's worker.

    The test Docker container runs an ArticleImportWorker on db=0. By using db=1
    for the in-process TestClient, queued URLs are invisible to the container's
    worker, preventing it from writing failed imports outside the test transaction.
    """
    client, session = txn_api_logged_in
    client.app.state.redis_client = test_redis
    yield client, session


class TestBulkImport:
    """Tests for bulk import API endpoints."""

    def test_bulk_import_submit(self, api_with_redis):
        """POST /articles/bulk-import/ returns 202 with batch_id."""
        client, _ = api_with_redis
        response = client.post(f'{ENDPOINT}bulk-import/', json={'urls': ['https://a.com', 'https://b.com']})
        assert response.status_code == status.HTTP_202_ACCEPTED, show_status_and_response(response)
        data = response.json()
        assert 'batch_id' in data
        assert data['total'] == 2
        assert data['status'] == 'queued'

    def test_bulk_import_no_urls_returns_400(self, api_with_redis):
        """POST /articles/bulk-import/ with empty urls returns 400."""
        client, _ = api_with_redis
        response = client.post(f'{ENDPOINT}bulk-import/', json={'urls': []})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_import_status(self, api_with_redis):
        """GET /articles/bulk-import/{batch_id}/ returns batch status."""
        client, _ = api_with_redis
        submit = client.post(f'{ENDPOINT}bulk-import/', json={'urls': ['https://c.com']})
        batch_id = submit.json()['batch_id']
        response = client.get(f'{ENDPOINT}bulk-import/{batch_id}/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['batch_id'] == batch_id
        assert data['total'] == 1
        assert data['status'] == 'queued'

    def test_bulk_import_nonexistent_batch_returns_404(self, api_with_redis):
        """GET /articles/bulk-import/{bad_id}/ returns 404."""
        client, _ = api_with_redis
        response = client.get(f'{ENDPOINT}bulk-import/nonexistent-id/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_failed_imports_empty(self, api_with_redis):
        """GET /articles/failed-imports/ returns empty list when none exist."""
        client, _ = api_with_redis
        response = client.get(f'{ENDPOINT}failed-imports/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []


class TestBulkImportUsageLimit:
    """The worker holds the queue when the Claude plan's usage limit refuses a call."""

    SUMMARIZE = 'ichrisbirch.api.endpoints.articles._summarize_and_create_article'

    def take_first_item(self, redis_client: redis.Redis) -> dict:
        popped = redis_client.blpop(QUEUE_KEY, timeout=1)
        assert popped is not None, 'the batch was not queued'
        _, item_json = popped
        return json.loads(item_json)

    def test_the_refused_item_goes_back_first_and_the_queue_pauses_until_the_reset(self, test_redis):
        batch_id = enqueue_bulk_import(test_redis, ['https://example.com/first', 'https://example.com/second'])
        worker = ArticleImportWorker(test_redis, get_settings())
        item = self.take_first_item(test_redis)
        resets_at = dt.datetime.now(dt.UTC) + dt.timedelta(hours=2)
        limit = AssistantUsageLimitReached('Article Summary with Tags', resets_at, 'five_hour')

        with patch(self.SUMMARIZE, side_effect=limit):
            worker._process_item(item)

        batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
        assert json.loads(test_redis.lindex(QUEUE_KEY, 0)) == item, 'the refused item keeps its place and its attempt count'
        assert test_redis.llen(QUEUE_KEY) == 2
        assert test_redis.get(PAUSE_KEY) == resets_at.isoformat()
        assert 7100 < test_redis.ttl(PAUSE_KEY) <= 7200, 'the pause expires when the limit resets'
        assert test_redis.ttl(batch_key) == -1, 'a batch still waiting has no expiry for the pause to outlast'
        assert test_redis.hget(batch_key, 'failed_count') == '0', 'a refused call is not a failed import'

    def test_a_limit_with_no_reset_time_holds_the_queue_for_the_recheck_interval(self, test_redis):
        enqueue_bulk_import(test_redis, ['https://example.com/only'])
        worker = ArticleImportWorker(test_redis, get_settings())
        item = self.take_first_item(test_redis)

        with patch(self.SUMMARIZE, side_effect=AssistantUsageLimitReached('Article Summary with Tags', None, None)):
            worker._process_item(item)

        recheck_seconds = int(USAGE_LIMIT_RECHECK.total_seconds())
        assert recheck_seconds - 5 < test_redis.ttl(PAUSE_KEY) <= recheck_seconds

    def test_a_batch_enqueued_during_a_long_pause_keeps_its_status_until_it_completes(self, test_redis):
        """A weekly limit can hold the queue for days, longer than a completed batch's status is kept."""
        pause_seconds = 3 * BATCH_TTL
        test_redis.set(PAUSE_KEY, (dt.datetime.now(dt.UTC) + dt.timedelta(seconds=pause_seconds)).isoformat(), ex=pause_seconds)
        batch_id = enqueue_bulk_import(test_redis, ['https://example.com/late'])
        batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
        assert test_redis.ttl(batch_key) == -1, 'the batch would expire while its URL still waits'

        worker = ArticleImportWorker(test_redis, get_settings())
        item = self.take_first_item(test_redis)
        with patch(self.SUMMARIZE, return_value=MagicMock(title='Late')):
            worker._process_item(item)

        assert test_redis.hget(batch_key, 'status') == 'completed'
        assert BATCH_TTL - 5 < test_redis.ttl(batch_key) <= BATCH_TTL, 'a completed batch is kept for a day'

    def test_an_item_whose_batch_is_gone_is_imported_without_recreating_the_batch(self, test_redis):
        """A write to a missing hash creates one with no total, which reads as completed and fails every status read."""
        batch_id = enqueue_bulk_import(test_redis, ['https://example.com/orphan'])
        batch_key = f'{BATCH_KEY_PREFIX}{batch_id}'
        item = self.take_first_item(test_redis)
        test_redis.delete(batch_key)
        worker = ArticleImportWorker(test_redis, get_settings())

        with patch(self.SUMMARIZE, return_value=MagicMock(title='Orphan')) as summarize:
            worker._process_item(item)

        summarize.assert_called_once()
        assert test_redis.exists(batch_key) == 0

    def test_a_paused_worker_takes_nothing_from_the_queue(self, test_redis):
        """A pause in Redis holds every worker, including one started after the limit was hit."""
        enqueue_bulk_import(test_redis, ['https://example.com/waiting'])
        test_redis.set(PAUSE_KEY, (dt.datetime.now(dt.UTC) + dt.timedelta(minutes=1)).isoformat(), ex=60)
        worker = ArticleImportWorker(test_redis, get_settings())

        with patch(self.SUMMARIZE, return_value=MagicMock(title='Taken')):
            worker.start()
            try:
                time.sleep(0.5)
                assert test_redis.llen(QUEUE_KEY) == 1, 'the worker took an item while paused'
            finally:
                worker.stop()

    def test_a_paused_batch_reports_when_it_resumes(self, api_with_redis, test_redis):
        client, _ = api_with_redis
        batch_id = client.post(f'{ENDPOINT}bulk-import/', json={'urls': ['https://example.com/held']}).json()['batch_id']
        resumes_at = (dt.datetime.now(dt.UTC) + dt.timedelta(hours=1)).isoformat()
        test_redis.set(PAUSE_KEY, resumes_at, ex=3600)

        data = client.get(f'{ENDPOINT}bulk-import/{batch_id}/').json()

        assert data['status'] == 'paused'
        assert data['resumes_at'] == resumes_at

    def test_a_completed_batch_is_not_reported_paused(self, api_with_redis, test_redis):
        client, _ = api_with_redis
        batch_id = client.post(f'{ENDPOINT}bulk-import/', json={'urls': ['https://example.com/done']}).json()['batch_id']
        test_redis.hset(f'{BATCH_KEY_PREFIX}{batch_id}', 'status', 'completed')
        test_redis.set(PAUSE_KEY, (dt.datetime.now(dt.UTC) + dt.timedelta(hours=1)).isoformat(), ex=3600)

        data = client.get(f'{ENDPOINT}bulk-import/{batch_id}/').json()

        assert data['status'] == 'completed'
        assert data['resumes_at'] is None
