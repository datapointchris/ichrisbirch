import json
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('articles')
    yield
    delete_test_data('articles')


NEW_OBJ = schemas.ArticleCreate(
    title='How to Use AI Agents',
    url='http://aiagents.com',
    tags=['ai agents', 'rag'],
    summary='AI agents are the future of computing.',
    save_date=datetime.now(),
)

ENDPOINT = '/articles/'

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


def test_read_current(test_api_logged_in):
    response = test_api_logged_in.get(f'{ENDPOINT}current/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is not None


def test_read_one_url(test_api_logged_in):
    # First create an article that we can query by URL
    response = test_api_logged_in.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    # Test getting article by URL
    response = test_api_logged_in.get(f'{ENDPOINT}url/', params={'url': NEW_OBJ.url})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    # Check if it's the expected article
    article = response.json()
    assert article is not None
    assert article['title'] == NEW_OBJ.title


def test_search(test_api_logged_in):
    # First create an article with specific tags for search testing
    searchable_article = schemas.ArticleCreate(
        title='Searchable Article',
        url='http://search-test.com',
        tags=['test-search', 'findable'],
        summary='This article should be found by search',
        save_date=datetime.now(),
    )
    response = test_api_logged_in.post(ENDPOINT, json=searchable_article.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    response = test_api_logged_in.get(f'{ENDPOINT}search/', params={'q': 'test-search'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    articles = response.json()
    assert len(articles) > 0
    assert any(article['title'] == 'Searchable Article' for article in articles)


@pytest.fixture
def mock_httpx_response():
    mock_response = MagicMock()
    mock_response.content = (
        '<html><head><title>Test Article | Website</title></head><body><p>Test content</p></body></html>'
    )
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_youtube_formatter():
    mock_formatter = MagicMock()
    mock_formatter.format_transcript.return_value = 'Test transcript text'
    return mock_formatter


@patch('httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi')
@patch('youtube_transcript_api.formatters.TextFormatter')
def test_summarize(
    mock_formatter_class, mock_yt_api, mock_httpx_get, mock_httpx_response, mock_youtube_formatter, test_api_logged_in
):
    # Setup mocks
    mock_httpx_get.return_value = mock_httpx_response
    mock_formatter_class.return_value = mock_youtube_formatter

    # We'll also mock our OpenAIAssistant to skip the actual call to the API
    with patch('ichrisbirch.ai.assistants.openai.OpenAIAssistant') as mock_assistant_class:
        mock_assistant = MagicMock()
        mock_assistant_class.return_value = mock_assistant

        # Create a specific expected response and force the mock to use it
        expected_summary = "Test summary"
        expected_tags = ["test", "article"]
        mock_assistant.generate.return_value = json.dumps({"summary": expected_summary, "tags": expected_tags})

        # Also patch the request object to ensure we get the right response
        with patch('ichrisbirch.api.endpoints.articles.OpenAIAssistant', return_value=mock_assistant):
            # Test article summarization
            response = test_api_logged_in.post(
                f'{ENDPOINT}summarize/', json={'url': 'https://example.com/test-article'}
            )
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

            # Verify response content
            data = response.json()
            assert data['title'] == 'Test Article'
            assert data['summary'] == expected_summary
            assert all(tag in data['tags'] for tag in expected_tags)


@patch('httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_insights(mock_get_transcript, mock_httpx_get, mock_httpx_response, test_api_logged_in):
    # Setup mocks
    mock_httpx_get.return_value = mock_httpx_response
    mock_get_transcript.return_value = [{'text': 'Test transcript', 'duration': 10}]

    # Mock OpenAI Assistant
    with patch('ichrisbirch.ai.assistants.openai.OpenAIAssistant') as mock_assistant_class:
        mock_assistant = MagicMock()
        # Ensure the exact formatting needed for the test
        mock_assistant.generate.return_value = '## Insights\n\nThis is a test insight.'
        mock_assistant_class.return_value = mock_assistant

        # Also patch the module-level import to make sure our mock is used
        with patch('ichrisbirch.api.endpoints.articles.OpenAIAssistant', return_value=mock_assistant):
            # Test article insights
            response = test_api_logged_in.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

            # Verify response contains HTML
            content = response.content.decode('utf-8')
            # The title would be "Test Article" stripped of whitespace
            assert '<h1>Test Article</h1>' in content
            # Check for the heading tag in the response
            assert '<h2>Insights</h2>' in content


def test_archive(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_id}/', json={'is_archived': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_unarchive(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_id}/', json={'is_archived': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_favorite(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_id}/', json={'is_favorite': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_unfavorite(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_id}/', json={'is_favorite': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read(test_api_logged_in):
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    article = test_api_logged_in.get(f'{ENDPOINT}{first_id}/').json()
    response = test_api_logged_in.patch(
        f'{ENDPOINT}{first_id}/',
        json={
            'is_current': False,
            'is_archived': True,
            'last_read_date': str(datetime.now()),
            'read_count': article.get('read_count') + 1,
        },
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
