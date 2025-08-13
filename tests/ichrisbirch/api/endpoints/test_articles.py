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
    response = test_api_logged_in.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    response = test_api_logged_in.get(f'{ENDPOINT}url/', params={'url': NEW_OBJ.url})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    article = response.json()
    assert article is not None
    assert article['title'] == NEW_OBJ.title


def test_search(test_api_logged_in):
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


@patch('ichrisbirch.api.endpoints.articles.httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi')
@patch('youtube_transcript_api.formatters.TextFormatter')
def test_summarize(mock_text_formatter, mock_yt_api, mock_httpx_get, test_api_logged_in):
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
            response = test_api_logged_in.post(f'{ENDPOINT}summarize/', json={'url': 'https://ichrisbirch.com/test-article'})
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
            data = response.json()
            assert data['title'] == 'Test Article'
            assert data['summary'] == expected_summary
            assert all(tag in data['tags'] for tag in expected_tags)


@patch('ichrisbirch.api.endpoints.articles.httpx.get')
@patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
def test_insights(mock_youtube_transcript_fetch, mock_httpx_get, test_api_logged_in):
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
            response = test_api_logged_in.post(f'{ENDPOINT}insights/', json={'url': 'https://example.com/test-article'})
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
            content = response.content.decode('utf-8')
            assert '<h1>Test Article</h1>' in content
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
