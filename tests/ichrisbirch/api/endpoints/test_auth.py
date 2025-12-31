import pytest
from fastapi import status

from ichrisbirch.api.endpoints.auth import validate_password
from ichrisbirch.api.endpoints.auth import validate_user_email
from ichrisbirch.api.endpoints.auth import validate_user_id
from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from tests.factories import UserFactory
from tests.utils.database import make_internal_service_headers
from tests.utils.database import make_invalid_internal_service_headers
from tests.utils.database import make_jwt_header
from tests.utils.database import test_settings

TEST_USER_PASSWORD = 'test_user_password'
ADMIN_USER_PASSWORD = 'admin_user_password'


@pytest.fixture
def auth_test_context(txn_api):
    """Provide transactional context with users for auth tests using factories."""
    client, session = txn_api
    # Create users with known passwords for testing
    regular_user = UserFactory(
        name='Regular Test User',
        email='regular@test.com',
        password=TEST_USER_PASSWORD,
    )
    admin_user = UserFactory(
        name='Admin Test User',
        email='admin@test.com',
        password=ADMIN_USER_PASSWORD,
        admin=True,
    )
    return client, session, regular_user, admin_user


@pytest.fixture
def test_user(auth_test_context):
    """Get the regular test user from the factory-created users."""
    _, _, regular_user, _ = auth_test_context
    return regular_user


@pytest.fixture
def test_admin_user(auth_test_context):
    """Get the admin test user from the factory-created users."""
    _, _, _, admin_user = auth_test_context
    return admin_user


@pytest.fixture
def jwt_handler(auth_test_context):
    """Create JWT handler using the transactional session."""
    _, session, _, _ = auth_test_context
    return JWTTokenHandler(settings=test_settings, session=session)


def test_validate_password(test_user):
    assert validate_password(test_user, TEST_USER_PASSWORD)
    assert not validate_password(test_user, 'wrong_password')


def test_validate_user_email(auth_test_context, test_user):
    _, session, _, _ = auth_test_context
    assert validate_user_email(test_user.email, session)
    assert validate_user_email('not.exist@example.com', session) is None


def test_validate_user_id(auth_test_context, test_user):
    _, session, _, _ = auth_test_context
    assert validate_user_id(test_user.get_id(), session) is not None
    assert validate_user_id('123456', session) is None


def test_generate_jwt(jwt_handler, test_user):
    token = jwt_handler.create_access_token(test_user.get_id())
    assert token
    assert isinstance(token, str)


def test_access_token_jwt_auth(auth_test_context, jwt_handler, test_user):
    client, _, _, _ = auth_test_context
    token = jwt_handler.create_access_token(test_user.get_id())
    headers = make_jwt_header(token)
    response = client.post('/auth/token/', headers=headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_access_token_oauth2(auth_test_context, test_user):
    client, _, _, _ = auth_test_context
    data = {'username': test_user.email, 'password': TEST_USER_PASSWORD}
    response = client.post('/auth/token/', data=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_validate_token(auth_test_context, jwt_handler, test_user):
    client, _, _, _ = auth_test_context
    token = jwt_handler.create_access_token(test_user.get_id())
    response = client.get('/auth/token/validate/', headers=make_jwt_header(token))
    assert response.status_code == status.HTTP_200_OK


def test_internal_service_authentication_valid(auth_test_context, test_user):
    """Test valid internal service authentication allows access to email endpoint."""
    client, _, _, _ = auth_test_context
    headers = make_internal_service_headers()
    response = client.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_user.email
    assert user_data['id'] == test_user.id


def test_internal_service_authentication_invalid_key(auth_test_context, test_user):
    """Test invalid internal service key returns 401."""
    client, _, _, _ = auth_test_context
    headers = make_invalid_internal_service_headers()
    response = client.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_headers(auth_test_context, test_user):
    """Test missing internal service headers returns 401."""
    client, _, _, _ = auth_test_context
    response = client.get(f'/users/email/{test_user.email}/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_service_header(auth_test_context, test_user):
    """Test missing X-Internal-Service header returns 401."""
    client, _, _, _ = auth_test_context
    headers = {'X-Service-Key': test_settings.auth.internal_service_key}
    response = client.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_internal_service_authentication_missing_key_header(auth_test_context, test_user):
    """Test missing X-Service-Key header returns 401."""
    client, _, _, _ = auth_test_context
    headers = {'X-Internal-Service': 'flask-frontend'}
    response = client.get(f'/users/email/{test_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']
