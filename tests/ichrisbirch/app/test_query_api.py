import logging
from unittest.mock import patch

import pytest
from fastapi import status

import tests.test_data
import tests.util
from ichrisbirch import schemas
from ichrisbirch.app.query_api import QueryAPI
from tests.util import show_status_and_response

NEW_USER = schemas.UserCreate(
    name='Test API Insert User',
    email='test.api.user@openai.com',
    password='stupidP@ssw0rd',
)

TEST_DATA = tests.test_data.users.BASE_DATA.copy()


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')
    yield
    tests.util.delete_test_data('users')


@pytest.fixture
def test_query_api():
    base_url = 'users'
    logger = logging.getLogger('test_query_api')
    response_model = schemas.User
    # mock_user = Mock()
    # mock_user.get_id.return_value = '123'
    return QueryAPI(base_url, logger, response_model)


@patch('ichrisbirch.app.utils.handle_if_not_response_code')
def test_get_one(mock_handle_if_not_response_code, test_query_api):
    mock_handle_if_not_response_code.return_value = None
    result = test_query_api.get_one('1')
    # annoyingly, the login users for the app are inserted first, before the test data
    assert result.name == tests.util.TEST_LOGIN_REGULAR_USER['name']


@patch('ichrisbirch.app.utils.handle_if_not_response_code')
def test_get_many(mock_handle_if_not_response_code, test_query_api):
    mock_handle_if_not_response_code.return_value = None
    result = test_query_api.get_many()
    assert isinstance(result, list)
    for r in result:
        assert r.name in (
            *[t.name for t in TEST_DATA],
            tests.util.TEST_LOGIN_REGULAR_USER['name'],
            tests.util.TEST_LOGIN_ADMIN_USER['name'],
        )


@patch('ichrisbirch.app.utils.handle_if_not_response_code')
def test_post(mock_handle_if_not_response_code, test_query_api):
    mock_handle_if_not_response_code.return_value = None
    result = test_query_api.post(json=NEW_USER.model_dump())
    assert result.name == NEW_USER.name

    results = test_query_api.get_many()
    assert len(results) == 6  # 2 app login users, 3 test users, 1 new user


@patch('ichrisbirch.app.utils.handle_if_not_response_code')
def test_patch(mock_handle_if_not_response_code, test_query_api):
    mock_handle_if_not_response_code.return_value = None
    new_name = 'User 1 Updated Name'
    result = test_query_api.patch('1', json={'name': new_name})
    assert result.name == new_name

    updated = test_query_api.get_one('1')
    assert updated.name == new_name


@patch('ichrisbirch.app.utils.handle_if_not_response_code')
def test_delete(mock_handle_if_not_response_code, test_query_api):
    mock_handle_if_not_response_code.return_value = None
    result = test_query_api.delete('1')
    assert result.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(result)
