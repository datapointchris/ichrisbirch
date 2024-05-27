import pytest
from fastapi import status

import tests.test_data
import tests.util
from ichrisbirch import models
from ichrisbirch.api.endpoints.auth import generate_jwt
from ichrisbirch.api.endpoints.auth import validate_password
from ichrisbirch.api.endpoints.auth import validate_user_email
from ichrisbirch.api.endpoints.auth import validate_user_id
from tests.conftest import settings


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')


@pytest.fixture()
def test_user():
    # look in tests.test_data.users to see user
    with tests.util.SessionTesting() as session:
        return session.get(models.User, 1)


@pytest.fixture()
def test_admin_user():
    # look in tests.test_data.users to see user is admin
    with tests.util.SessionTesting() as session:
        return session.get(models.User, 3)


def make_app_headers_for_user(user: models.User):
    return {'X-Application-ID': settings.flask.app_id, 'X-User-ID': user.get_id()}


def make_jwt_header(token: str):
    return {'Authorization': f'Bearer {token}'}


def test_validate_password(test_user):
    assert validate_password(test_user, 'regular_user_1_password')
    assert not validate_password(test_user, 'wrong_password')


def test_validate_user_email(test_user):
    with tests.util.SessionTesting() as session:
        assert validate_user_email(test_user.email, session)
        assert validate_user_email('not.exist@example.com', session) is None


def test_validate_user_id(test_user):
    with tests.util.SessionTesting() as session:
        assert validate_user_id(test_user.get_id(), session) is not None
        assert validate_user_id('123456', session) is None


def test_generate_jwt(test_user):
    token = generate_jwt(test_user.id)
    assert token
    assert isinstance(token, str)


def test_access_token_application_headers(test_api, test_user):
    headers = make_app_headers_for_user(test_user)
    response = test_api.post('/auth/token/', headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert 'access_token' in response.json()


def test_access_token_jwt_auth(test_api, test_user):
    token = generate_jwt(test_user.get_id())
    headers = make_jwt_header(token)
    response = test_api.post('/auth/token/', headers=headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_access_token_oauth2(test_api, test_user):
    data = {'username': test_user.email, 'password': 'regular_user_1_password'}
    response = test_api.post('/auth/token/', data=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_validate_token(test_api, test_user):
    token = generate_jwt(test_user.get_id())
    response = test_api.get('/auth/token/validate/', headers={'token': token})
    assert response.status_code == status.HTTP_200_OK
