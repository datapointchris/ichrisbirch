from datetime import datetime

import pytest
from fastapi import status

import tests.util
from ichrisbirch import schemas
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('articles')
    yield
    tests.util.delete_test_data('articles')


NEW_OBJ = schemas.ArticleCreate(
    title='How to Use AI Agents',
    url='http://aiagents.com',
    tags=['ai agents', 'rag'],
    summary='AI agents are the future of computing.',
    save_date=datetime.now(),
)

ENDPOINT = '/articles/'

crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in, verify_attr='title')


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in, verify_attr='title')


def test_read_current(test_api_logged_in):
    response = test_api_logged_in.get(f'{ENDPOINT}current/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() is not None


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
