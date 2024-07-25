from datetime import datetime

import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('articles')


NEW_ARTICLE = schemas.ArticleCreate(
    title='How to Use AI Agents',
    url='http://aiagents.com',
    tags=['ai agents', 'rag'],
    summary='AI agents are the future of computing.',
    save_date=datetime.now(),
)


def test_read_many_articles(test_api):
    response = test_api.get('/articles/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) > 0


def test_read_current_article(test_api):
    response = test_api.get('/articles/current/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is not None


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_read_one_article(test_api, article_id):
    response = test_api.get(f'/articles/{article_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_create_article(test_api):
    response = test_api.post('/articles/', content=NEW_ARTICLE.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['title'] == NEW_ARTICLE.title

    # Test article was created
    created = test_api.get('/articles/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) > 0


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_delete_article(test_api, article_id):
    endpoint = f'/articles/{article_id}/'
    article = test_api.get(endpoint)
    assert article.status_code == status.HTTP_200_OK, show_status_and_response(article)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_archive_article(test_api, article_id):
    response = test_api.patch(f'/articles/{article_id}/', json={'is_archived': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_unarchive_article(test_api, article_id):
    response = test_api.patch(f'/articles/{article_id}/', json={'is_archived': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_favorite_article(test_api, article_id):
    response = test_api.patch(f'/articles/{article_id}/', json={'is_favorite': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_unfavorite_article(test_api, article_id):
    response = test_api.patch(f'/articles/{article_id}/', json={'is_favorite': False})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize('article_id', [1, 2, 3])
def test_read_article(test_api, article_id):
    article = test_api.get(f'/articles/{article_id}/').json()
    response = test_api.patch(
        f'/articles/{article_id}',
        json={
            'is_current': False,
            'is_archived': True,
            'last_read_date': str(datetime.now()),
            'read_count': article.get('read_count') + 1,
        },
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
