import pytest
from fastapi import status

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from tests.factories import UserFactory
from tests.util import show_status_and_response
from tests.utils.database import get_test_login_users
from tests.utils.database import make_app_headers_for_user
from tests.utils.database import make_internal_service_headers
from tests.utils.database import make_invalid_internal_service_headers
from tests.utils.database import make_jwt_header
from tests.utils.database import test_settings

from .crud_test import ApiCrudTester

DEFAULT_USER_PREFERENCES = models.User.default_preferences()
ENDPOINT = '/users/'

# Factory-created users count (3 regular + admin replaces the old BASE_DATA approach)
NUM_FACTORY_USERS = 3
NUM_LOGIN_USERS = len(get_test_login_users())
EXPECTED_LENGTH = NUM_LOGIN_USERS + NUM_FACTORY_USERS

# Test user credentials for factory creation
TEST_USERS = [
    {'name': 'Regular User 1', 'email': 'regular_user_1@test.com', 'password': 'regular_user_1_password', 'is_admin': False},
    {'name': 'Regular User 2', 'email': 'regular_user_2@test.com', 'password': 'regular_user_2_password', 'is_admin': False},
    {'name': 'Admin User', 'email': 'admin@test.com', 'password': 'admin_password', 'is_admin': True},
]
TEST_USER_EMAILS = [u['email'] for u in TEST_USERS]

NEW_OBJ = schemas.UserCreate(
    name='Test API Insert User',
    email='test.api.user@openai.com',
    password='stupidP@ssw0rd',
)


def create_test_users():
    """Create standard test users using factories.

    Returns dict of created users keyed by role for easy access.
    """
    users = {}
    for user_data in TEST_USERS:
        user = UserFactory(
            name=user_data['name'],
            email=user_data['email'],
            password=user_data['password'],
            is_admin=user_data['is_admin'],
        )
        # Store by role for easy access
        if user_data['is_admin']:
            users['admin'] = user
        elif 'User 1' in user_data['name']:
            users['regular_1'] = user
        else:
            users['regular_2'] = user
    return users


@pytest.fixture
def users_test_context(txn_api):
    """Provide transactional context with factory-created users."""
    client, session = txn_api
    users = create_test_users()
    return client, session, users


@pytest.fixture
def users_logged_in_context(txn_api_logged_in):
    """Provide transactional context with factory-created users for logged-in tests."""
    client, session = txn_api_logged_in
    users = create_test_users()
    return client, session, users


@pytest.fixture
def users_admin_context(txn_api_logged_in_admin):
    """Provide transactional context with factory-created users for admin tests."""
    client, session = txn_api_logged_in_admin
    users = create_test_users()
    return client, session, users


@pytest.fixture
def test_regular_user(users_test_context):
    """Get the primary regular test user."""
    _, _, users = users_test_context
    return users['regular_1']


@pytest.fixture
def test_regular_user_2(users_test_context):
    """Get a regular test user (different from test_regular_user for testing cross-user access)."""
    _, _, users = users_test_context
    return users['regular_2']


@pytest.fixture
def test_admin_user(users_test_context):
    """Get admin test user."""
    _, _, users = users_test_context
    return users['admin']


@pytest.fixture
def jwt_handler(users_test_context):
    """Create JWT handler using the transactional session."""
    _, session, _ = users_test_context
    return JWTTokenHandler(settings=test_settings, session=session)


def test_read_one_requires_admin_or_internal_service(users_logged_in_context):
    """Test that regular users cannot access other users by ID."""
    client, _, _ = users_logged_in_context
    response = client.get(f'{ENDPOINT}1/')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only access your own user data' in response.json()['detail']


def test_read_many_regular_user_unauthorized(users_logged_in_context):
    client, _, _ = users_logged_in_context
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=EXPECTED_LENGTH)
    with pytest.raises(AssertionError):
        crud_tests.test_read_many(client)


def test_read_many_unauthorized_user(users_logged_in_context):
    client, _, _ = users_logged_in_context
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_many_admin_user_authorized(users_admin_context):
    client, _, _ = users_admin_context
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=EXPECTED_LENGTH)
    crud_tests.test_read_many(client)


def test_create(txn_multi_client):
    """Test user creation using multi-client fixture to avoid transaction deadlock."""
    ctx = txn_multi_client
    create_test_users()  # Use factory instead of insert_test_data_transactional

    client = ctx['client_logged_in']
    admin_client = ctx['client_admin']

    created = client.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)

    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=EXPECTED_LENGTH)
    crud_tests._verify_attribute(created, crud_tests.verify_attr)

    all_users = admin_client.get(ENDPOINT)
    assert all_users.status_code == status.HTTP_200_OK, show_status_and_response(all_users)
    crud_tests._verify_length(all_users, EXPECTED_LENGTH + 1)


def test_delete(users_admin_context):
    client, _, _ = users_admin_context
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=EXPECTED_LENGTH)

    all_before_delete = client.get(ENDPOINT)
    assert all_before_delete.status_code == status.HTTP_200_OK, show_status_and_response(all_before_delete)
    crud_tests._verify_length(all_before_delete, EXPECTED_LENGTH)

    first_id = all_before_delete.json()[0]['id']
    response = client.delete(f'{ENDPOINT}{first_id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    all_after_delete = client.get(ENDPOINT)
    assert all_after_delete.status_code == status.HTTP_200_OK, show_status_and_response(all_after_delete)
    crud_tests._verify_length(all_after_delete, EXPECTED_LENGTH - 1)


def test_patch_user(txn_multi_client):
    """Test that a logged-in user can update another user only if they are admin."""
    ctx = txn_multi_client
    create_test_users()  # Use factory instead of insert_test_data_transactional

    client = ctx['client_logged_in']
    admin_client = ctx['client_admin']

    # First, create a new user to update
    created = client.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    user_id = created.json()['id']

    # Admin should be able to update any user
    new_name = 'Updated User 1 Name'
    response = admin_client.patch(f'{ENDPOINT}{user_id}/', json={'name': new_name})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['name'] == new_name


@pytest.mark.parametrize('email', TEST_USER_EMAILS)
def test_read_one_user_by_email(users_test_context, email):
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    response = client.get(f'/users/email/{email}/', headers=headers)
    user = schemas.User(**response.json())
    assert user.email == email


def test_read_one_user_by_alt_id(users_logged_in_context):
    """Since alternative id is assigned by the database, get the user by /me/ then query with alternative id and see if they match."""
    client, _, _ = users_logged_in_context

    # Get user details via /me/ endpoint
    response = client.get('/users/me/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    me_user = schemas.User(**response.json())

    # Now get the same user by alternative ID
    response = client.get(f'/users/alt/{me_user.alternative_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    alt_user = schemas.User(**response.json())

    # Verify both responses contain the same user
    assert me_user == alt_user


def test_user_set_password():
    user = models.User(**NEW_OBJ.model_dump())
    # should not be hashed yet, hasn't been inserted in db
    assert user.password == NEW_OBJ.password
    user.set_password(user.password)  # hash and re-assign to self
    assert user.password != NEW_OBJ.password
    assert user.check_password(NEW_OBJ.password)


def test_create_user_password_hashed(users_logged_in_context):
    client, _, _ = users_logged_in_context
    created_response = client.post('/users/', content=NEW_OBJ.model_dump_json())
    assert created_response.status_code == status.HTTP_201_CREATED, show_status_and_response(created_response)
    created_user = models.User(**created_response.json())
    assert created_user.name == NEW_OBJ.name
    # password should be hashed since it was inserted in the db and not match original
    assert created_user.password != NEW_OBJ.password
    # but hashing original password should match
    assert created_user.check_password(NEW_OBJ.password)


@pytest.mark.parametrize('user_data', TEST_USERS)
def test_check_user_password_functions(users_test_context, user_data):
    """When creating new users, the password should be hashed by the model in the post endpoint and stored in the database as the hash.

    Retrieving those passwords and comparing them to the User.check_password output with the original passwords from the testing data should
    be equivalent. Users need to be retrieved by email since id and alternative_id are both assigned by the db and not available in the
    testing data
    """
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    response = client.get(f'/users/email/{user_data["email"]}/', headers=headers)
    db_user = models.User(**response.json())
    assert db_user.check_password(user_data['password'])


def test_get_user_me(users_logged_in_context):
    """Test the /me/ endpoint to get the current user's information."""
    client, _, _ = users_logged_in_context
    response = client.get('/users/me/')
    assert response.status_code == status.HTTP_200_OK
    user = schemas.User(**response.json())
    assert user.name == 'Test Login Regular User'


def test_get_user_me_application_headers(users_test_context, test_regular_user):
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user)
    response = client.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_regular_user.name


def test_get_user_me_jwt(users_test_context, test_regular_user):
    """Send a request to /auth/token/ to get a token using oauth2 username and password.

    Then use the token to get /me/ endpoint
    """
    client, _, _ = users_test_context
    # Use the password from TEST_USERS for Regular User 1
    user_1_password = TEST_USERS[0]['password']
    data = {'username': test_regular_user.email, 'password': user_1_password}
    response = client.post('/auth/token/', data=data)
    token = response.json()['access_token']
    headers = make_jwt_header(token)
    response = client.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_regular_user.name


def get_pref_value(preferences, key):
    """Get the value of a nested key in a dictionary."""
    keys = key.split('.')
    value = preferences
    for k in keys:
        value = value.get(k)
    return value


def assert_preference_key_equal(preferences, default_preferences, key):
    pref_value = get_pref_value(preferences, key)
    default_pref_value = get_pref_value(default_preferences, key)
    assert pref_value == default_pref_value, f'Expected {key} to be {default_pref_value}, but got {pref_value}'


def test_update_user_simple_preferences_valid(users_logged_in_context):
    client, _, _ = users_logged_in_context
    new_preferences = {'theme_color': 'green', 'notifications': True}
    response = client.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    assert updated_user.preferences['theme_color'] == new_preferences['theme_color']
    assert updated_user.preferences['notifications'] == new_preferences['notifications']
    # Make sure defaults weren't erased
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_by_id_simple_preferences_valid(users_logged_in_context):
    """Test updating the current user's preferences using the /me/ endpoint."""
    client, _, _ = users_logged_in_context
    # Update the logged-in user's preferences
    new_preferences = {'theme_color': 'green', 'notifications': True}
    response = client.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    assert updated_user.preferences['theme_color'] == new_preferences['theme_color']
    assert updated_user.preferences['notifications'] == new_preferences['notifications']
    # Make sure defaults weren't erased
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_preferences_deep_nested_key(users_logged_in_context):
    """Test updating user preferences with a deep nested key."""
    client, _, _ = users_logged_in_context
    new_preferences = {'box_packing': {'pages': {'all': {'view_type': 'compact'}}}}
    response = client.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, new_preferences, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_preferences_invalid_key(users_logged_in_context):
    """Test updating user preferences with an invalid key."""
    client, _, _ = users_logged_in_context
    invalid_preferences = {'invalid_key': 'value'}
    response = client.patch('/users/me/preferences/', json=invalid_preferences)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_data = response.json()
    assert 'detail' in error_data


def test_update_user_preferences_invalid_value(users_logged_in_context):
    """Test updating user preferences with invalid data."""
    client, _, _ = users_logged_in_context
    invalid_preferences = {'theme': 'invalid_theme', 'notifications': True}
    response = client.patch('/users/me/preferences/', json=invalid_preferences)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_data = response.json()
    assert 'detail' in error_data


def test_list_users_requires_admin_or_internal_service(users_test_context, test_regular_user_2):
    """Test that regular users cannot list all users."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user_2)
    response = client.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_list_users_allows_admin(users_test_context, test_admin_user):
    """Test that admin users can list all users."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    response = client.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) > 0


def test_list_users_allows_internal_service(users_test_context):
    """Test that internal service can list all users."""
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    response = client.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) > 0


def test_read_user_by_id_requires_own_data_or_admin(users_test_context, test_regular_user_2, test_regular_user):
    """Test that users can only read their own data unless they're admin."""
    client, _, _ = users_test_context
    # Regular user trying to access another user's data
    headers = make_app_headers_for_user(test_regular_user_2)
    response = client.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only access your own user data' in response.json()['detail']


def test_read_user_by_id_allows_own_data(users_test_context, test_regular_user):
    """Test that users can read their own data."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user)
    response = client.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id
    assert user_data['email'] == test_regular_user.email


def test_read_user_by_id_allows_admin(users_test_context, test_admin_user, test_regular_user):
    """Test that admin users can read any user's data."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    response = client.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id


def test_read_user_by_id_allows_internal_service(users_test_context, test_regular_user):
    """Test that internal service can read any user's data."""
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    response = client.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id


def test_read_user_by_email_requires_admin_or_internal_service(users_test_context, test_regular_user_2, test_regular_user):
    """Test that regular users cannot look up users by email."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user_2)
    response = client.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_read_user_by_email_requires_internal_service_only(users_test_context, test_admin_user, test_regular_user):
    """Test that admin users can look up users by email."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    response = client.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_regular_user.email


def test_read_user_by_email_allows_internal_service(users_test_context, test_regular_user):
    """Test that internal service can look up users by email."""
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    response = client.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_regular_user.email


def test_update_user_requires_own_data_or_admin(users_test_context, test_regular_user_2, test_regular_user):
    """Test that users can only update their own data unless they're admin."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user_2)
    update_data = {'name': 'Updated Name'}
    response = client.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only update your own user data' in response.json()['detail']


def test_update_user_allows_own_data(users_test_context, test_regular_user):
    """Test that users can update their own data."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user)
    update_data = {'name': 'Updated Name'}
    response = client.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Updated Name'


def test_update_user_allows_admin(users_test_context, test_admin_user, test_regular_user):
    """Test that admin users can update any user's data."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    update_data = {'name': 'Admin Updated Name'}
    response = client.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Admin Updated Name'


def test_update_user_allows_internal_service(users_test_context, test_regular_user):
    """Test that internal service can update any user's data."""
    client, _, _ = users_test_context
    headers = make_internal_service_headers()
    update_data = {'name': 'Service Updated Name'}
    response = client.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Service Updated Name'


def test_delete_user_requires_admin_or_internal_service(users_test_context, test_regular_user_2, test_regular_user):
    """Test that regular users cannot delete any users."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user_2)
    response = client.delete(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'Admin access required' in response.json()['detail']


def test_delete_user_prevents_self_deletion(users_test_context, test_admin_user):
    """Test that even admin users cannot delete themselves."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    response = client.delete(f'/users/{test_admin_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'Cannot delete your own account' in response.json()['detail']


def test_update_user_preferences_requires_own_data_or_admin(users_test_context, test_regular_user_2, test_regular_user):
    """Test that users can only update their own preferences unless they're admin."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user_2)
    update_data = {'dark_mode': True}
    response = client.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only update your own preferences' in response.json()['detail']


def test_update_user_preferences_allows_own_data(users_test_context, test_regular_user):
    """Test that users can update their own preferences."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_regular_user)
    update_data = {'dark_mode': True}
    response = client.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['preferences']['dark_mode'] is True


def test_update_user_preferences_allows_admin(users_test_context, test_admin_user, test_regular_user):
    """Test that admin users can update any user's preferences."""
    client, _, _ = users_test_context
    headers = make_app_headers_for_user(test_admin_user)
    update_data = {'dark_mode': True}
    response = client.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['preferences']['dark_mode'] is True


def test_internal_service_auth_invalid_key(users_test_context, test_regular_user_2):
    """Test that invalid internal service key returns 401."""
    client, _, _ = users_test_context
    headers = make_invalid_internal_service_headers()
    response = client.get(f'/users/{test_regular_user_2.id}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Authentication required' in response.json()['detail']


def test_no_authentication_returns_401(users_test_context, test_regular_user_2):
    """Test that requests without authentication return 401."""
    client, _, _ = users_test_context
    response = client.get(f'/users/{test_regular_user_2.id}/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_jwt_authentication_works(users_test_context, test_regular_user_2, jwt_handler):
    """Test that JWT authentication works for user endpoints."""
    client, _, _ = users_test_context
    token = jwt_handler.create_access_token(test_regular_user_2.get_id())
    headers = make_jwt_header(token)
    response = client.get(f'/users/{test_regular_user_2.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user_2.id
