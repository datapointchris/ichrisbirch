import pytest
from fastapi import status

import tests.test_data
from ichrisbirch.api.endpoints.auth import validate_password
from ichrisbirch.api.endpoints.auth import validate_user_email
from ichrisbirch.api.endpoints.auth import validate_user_id
from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from ichrisbirch.database.sqlalchemy.session import create_session
from tests.utils.database import delete_test_data
from tests.utils.database import get_test_user
from tests.utils.database import insert_test_data
from tests.utils.database import make_internal_service_headers
from tests.utils.database import make_invalid_internal_service_headers
from tests.utils.database import make_jwt_header
from tests.utils.database import test_settings

USERS_TEST_DATA = tests.test_data.users.BASE_DATA


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('users')
    yield
    delete_test_data('users')


@pytest.fixture()
def test_user():
    return get_test_user('regular_user_1@gmail.com')


@pytest.fixture()
def test_admin_user():
    return get_test_user('admin@admin.com')


@pytest.fixture()
def jwt_handler():
    with create_session(test_settings) as test_session:
        return JWTTokenHandler(settings=test_settings, session=test_session)


def test_validate_password(test_user):
    assert validate_password(test_user, USERS_TEST_DATA[0].password)
    assert not validate_password(test_user, 'wrong_password')


def test_validate_user_email(test_user):
    with create_session(test_settings) as session:
        assert validate_user_email(test_user.email, session)
        assert validate_user_email('not.exist@example.com', session) is None


def test_validate_user_id(test_user):
    with create_session(test_settings) as session:
        assert validate_user_id(test_user.get_id(), session) is not None
        assert validate_user_id('123456', session) is None


def test_generate_jwt(jwt_handler, test_user):
    token = jwt_handler.create_access_token(test_user.get_id())
    assert token
    assert isinstance(token, str)


def test_access_token_jwt_auth(test_api_function, jwt_handler, test_user):
    token = jwt_handler.create_access_token(test_user.get_id())
    headers = make_jwt_header(token)
    response = test_api_function.post('/auth/token/', headers=headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_access_token_oauth2(test_api_function, test_user):
    data = {'username': test_user.email, 'password': USERS_TEST_DATA[0].password}
    response = test_api_function.post('/auth/token/', data=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_validate_token(test_api_function, jwt_handler, test_user):
    token = jwt_handler.create_access_token(test_user.get_id())
    response = test_api_function.get('/auth/token/validate/', headers=make_jwt_header(token))
    assert response.status_code == status.HTTP_200_OK


# =============================================================================
# INTERNAL SERVICE AUTHENTICATION TESTS
# =============================================================================


def test_internal_service_authentication_valid(test_api_function, test_user):
    """Test valid internal service authentication allows access to email endpoint."""
    headers = make_internal_service_headers()
    response = test_api_function.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_user.email
    assert user_data['id'] == test_user.id


def test_internal_service_authentication_invalid_key(test_api_function, test_user):
    """Test invalid internal service key returns 401."""
    headers = make_invalid_internal_service_headers()
    response = test_api_function.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_headers(test_api_function, test_user):
    """Test missing internal service headers returns 401."""
    response = test_api_function.get(f'/users/email/{test_user.email}/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_service_header(test_api_function, test_user):
    """Test missing X-Internal-Service header returns 401."""
    from tests.utils.database import test_settings

    headers = {'X-Service-Key': test_settings.auth.internal_service_key}
    response = test_api_function.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_key_header(test_api_function, test_user):
    """Test missing X-Service-Key header returns 401."""
    headers = {'X-Internal-Service': 'flask-frontend'}
    response = test_api_function.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']
