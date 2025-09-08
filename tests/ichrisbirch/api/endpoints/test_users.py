import pytest
from fastapi import status

import tests.test_data
from ichrisbirch import models
from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import create_jwt_handler
from tests.utils.database import delete_test_data
from tests.utils.database import get_test_data_admin_user
from tests.utils.database import get_test_data_regular_user
from tests.utils.database import get_test_data_regular_user_2
from tests.utils.database import get_test_login_users
from tests.utils.database import insert_test_data
from tests.utils.database import make_app_headers_for_user
from tests.utils.database import make_internal_service_headers
from tests.utils.database import make_invalid_internal_service_headers
from tests.utils.database import make_jwt_header

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('users')
    yield
    delete_test_data('users')


@pytest.fixture()
def test_user():
    """Fixture to get a regular test user (different from test_regular_user for testing cross-user access)."""
    return get_test_data_regular_user_2()


@pytest.fixture()
def test_regular_user():
    """Fixture to get the primary regular test user."""
    return get_test_data_regular_user()


@pytest.fixture()
def test_admin_user():
    """Fixture to get admin test user."""
    return get_test_data_admin_user()


@pytest.fixture()
def jwt_handler():
    """Fixture to create JWT token handler."""
    return create_jwt_handler()


DEFAULT_USER_PREFERENCES = models.User.default_preferences()
TEST_DATA_USERS = tests.test_data.users.BASE_DATA
TEST_DATA_EMAILS = [user.email for user in TEST_DATA_USERS]
ENDPOINT = '/users/'
EXPECTED_LENGTH = len(get_test_login_users()) + 3
NEW_OBJ = schemas.UserCreate(
    name='Test API Insert User',
    email='test.api.user@openai.com',
    password='stupidP@ssw0rd',
)


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, expected_length=EXPECTED_LENGTH)


def test_read_one_requires_admin_or_internal_service(test_api_logged_in):
    """Test that regular users cannot access other users by ID."""
    response = test_api_logged_in.get(f'{ENDPOINT}1/')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only access your own user data' in response.json()['detail']


def test_read_many_regular_user_unauthorized(test_api_logged_in):
    with pytest.raises(AssertionError):
        crud_tests.test_read_many(test_api_logged_in)


def test_read_many_unauthorized_user(test_api_logged_in):
    response = test_api_logged_in.get(ENDPOINT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_many_admin_user_authorized(test_api_logged_in_admin):
    crud_tests.test_read_many(test_api_logged_in_admin)


def test_create(test_api_logged_in, test_api_logged_in_admin):
    created = test_api_logged_in.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    crud_tests._verify_attribute(created, crud_tests.verify_attr)

    all = test_api_logged_in_admin.get(ENDPOINT)
    assert all.status_code == status.HTTP_200_OK, show_status_and_response(all)
    crud_tests._verify_length(all, EXPECTED_LENGTH + 1)


def test_delete(test_api_logged_in, test_api_logged_in_admin):
    all_before_delete = test_api_logged_in_admin.get(ENDPOINT)
    assert all_before_delete.status_code == status.HTTP_200_OK, show_status_and_response(all_before_delete)
    crud_tests._verify_length(all_before_delete, EXPECTED_LENGTH)

    first_id = all_before_delete.json()[0]['id']
    response = test_api_logged_in_admin.delete(f'{ENDPOINT}{first_id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    all_after_delete = test_api_logged_in_admin.get(ENDPOINT)
    assert all_after_delete.status_code == status.HTTP_200_OK, show_status_and_response(all_after_delete)
    crud_tests._verify_length(all_after_delete, EXPECTED_LENGTH - 1)


def test_patch_user(test_api_logged_in, test_api_logged_in_admin):
    """Test that a logged-in user can update another user only if they are admin."""
    # First, create a new user to update
    created = test_api_logged_in.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    user_id = created.json()['id']

    # Admin should be able to update any user
    new_name = 'Updated User 1 Name'
    response = test_api_logged_in_admin.patch(f'{ENDPOINT}{user_id}/', json={'name': new_name})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['name'] == new_name


@pytest.mark.parametrize('email', TEST_DATA_EMAILS)
def test_read_one_user_by_email(test_api_function, email):
    headers = make_internal_service_headers()
    response = test_api_function.get(f'/users/email/{email}/', headers=headers)
    user = schemas.User(**response.json())
    assert user.email == email


def test_read_one_user_by_alt_id(test_api_logged_in):
    """Since alternative id is assigned by the database, get the user by /me/ then query with alternative id and see if they match."""
    # Get user details via /me/ endpoint
    response = test_api_logged_in.get('/users/me/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    me_user = schemas.User(**response.json())

    # Now get the same user by alternative ID
    response = test_api_logged_in.get(f'/users/alt/{me_user.alternative_id}/')
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


def test_create_user_password_hashed(test_api_logged_in):
    created_response = test_api_logged_in.post('/users/', content=NEW_OBJ.model_dump_json())
    assert created_response.status_code == status.HTTP_201_CREATED, show_status_and_response(created_response)
    created_user = models.User(**created_response.json())
    assert created_user.name == NEW_OBJ.name
    # password should be hashed since it was inserted in the db and not match original
    assert created_user.password != NEW_OBJ.password
    # but hashing original password should match
    assert created_user.check_password(NEW_OBJ.password)


@pytest.mark.parametrize('user', TEST_DATA_USERS)
def test_check_user_password_functions(test_api_function, user):
    """When creating new users, the password should be hashed by the model in the post endpoint and stored in the database as the hash.

    Retrieving those passwords and comparing them to the User.check_password output with the original passwords from the testing data should
    be equivalent. Users need to be retrieved by email since id and alternative_id are both assigned by the db and not available in the
    testing data
    """
    headers = make_internal_service_headers()
    response = test_api_function.get(f'/users/email/{user.email}/', headers=headers)
    db_user = models.User(**response.json())
    assert db_user.check_password(user.password)


def test_get_user_me(test_api_logged_in):
    """Test the /me/ endpoint to get the current user's information."""
    response = test_api_logged_in.get('/users/me/')
    assert response.status_code == status.HTTP_200_OK
    user = schemas.User(**response.json())
    assert user.name == 'Test Login Regular User'


def test_get_user_me_application_headers(test_api_function, test_regular_user):
    headers = make_app_headers_for_user(test_regular_user)
    response = test_api_function.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_regular_user.name


def test_get_user_me_jwt(test_api_function, test_regular_user):
    """Send a request to /auth/token/ to get a token using oauth2 username and password.

    Then use the token to get /me/ endpoint
    """
    data = {'username': test_regular_user.email, 'password': 'regular_user_1_password'}
    response = test_api_function.post('/auth/token/', data=data)
    token = response.json()['access_token']
    headers = make_jwt_header(token)
    response = test_api_function.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_regular_user.name


def get_pref_value(preferencces, key):
    """Get the value of a nested key in a dictionary."""
    keys = key.split('.')
    value = preferencces
    for k in keys:
        value = value.get(k)
    return value


def assert_preference_key_equal(preferences, default_preferences, key):
    pref_value = get_pref_value(preferences, key)
    default_pref_value = get_pref_value(default_preferences, key)
    assert pref_value == default_pref_value, f'Expected {key} to be {default_pref_value}, but got {pref_value}'


def test_update_user_simple_preferences_valid(test_api_logged_in):
    new_preferences = {'theme_color': 'green', 'notifications': True}
    response = test_api_logged_in.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    assert updated_user.preferences['theme_color'] == new_preferences['theme_color']
    assert updated_user.preferences['notifications'] == new_preferences['notifications']
    # Make sure defaults weren't erased
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_by_id_simple_preferences_valid(test_api_logged_in):
    """Test updating the current user's preferences using the /me/ endpoint."""
    # Update the logged-in user's preferences
    new_preferences = {'theme_color': 'green', 'notifications': True}
    response = test_api_logged_in.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    assert updated_user.preferences['theme_color'] == new_preferences['theme_color']
    assert updated_user.preferences['notifications'] == new_preferences['notifications']
    # Make sure defaults weren't erased
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_preferences_deep_nested_key(test_api_logged_in):
    """Test updating user preferences with a deep nested key."""
    new_preferences = {'box_packing': {'pages': {'all': {'view_type': 'compact'}}}}
    response = test_api_logged_in.patch('/users/me/preferences/', json=new_preferences)
    assert response.status_code == status.HTTP_200_OK
    updated_user = schemas.User(**response.json())
    key = 'box_packing.pages.all.view_type'
    assert_preference_key_equal(updated_user.preferences, new_preferences, key)
    key = 'tasks.pages.index.view_type'
    assert_preference_key_equal(updated_user.preferences, DEFAULT_USER_PREFERENCES, key)


def test_update_user_preferences_invalid_key(test_api_logged_in):
    """Test updating user preferences with an invalid key."""
    invalid_preferences = {'invalid_key': 'value'}
    response = test_api_logged_in.patch('/users/me/preferences/', json=invalid_preferences)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_data = response.json()
    assert 'detail' in error_data


def test_update_user_preferences_invalid_value(test_api_logged_in):
    """Test updating user preferences with invalid data."""
    invalid_preferences = {'theme': 'invalid_theme', 'notifications': True}
    response = test_api_logged_in.patch('/users/me/preferences/', json=invalid_preferences)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_data = response.json()
    assert 'detail' in error_data


# =============================================================================
# AUTHORIZATION TESTS
# =============================================================================


def test_list_users_requires_admin_or_internal_service(test_api_function, test_user):
    """Test that regular users cannot list all users."""
    headers = make_app_headers_for_user(test_user)
    response = test_api_function.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_list_users_allows_admin(test_api_function, test_admin_user):
    """Test that admin users can list all users."""
    headers = make_app_headers_for_user(test_admin_user)
    response = test_api_function.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) > 0


def test_list_users_allows_internal_service(test_api_function):
    """Test that internal service can list all users."""
    headers = make_internal_service_headers()
    response = test_api_function.get('/users/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) > 0


def test_read_user_by_id_requires_own_data_or_admin(test_api_function, test_user, test_regular_user):
    """Test that users can only read their own data unless they're admin."""
    # Regular user trying to access another user's data
    headers = make_app_headers_for_user(test_user)
    response = test_api_function.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only access your own user data' in response.json()['detail']


def test_read_user_by_id_allows_own_data(test_api_function, test_regular_user):
    """Test that users can read their own data."""
    headers = make_app_headers_for_user(test_regular_user)
    response = test_api_function.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id
    assert user_data['email'] == test_regular_user.email


def test_read_user_by_id_allows_admin(test_api_function, test_admin_user, test_regular_user):
    """Test that admin users can read any user's data."""
    headers = make_app_headers_for_user(test_admin_user)
    response = test_api_function.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id


def test_read_user_by_id_allows_internal_service(test_api_function, test_regular_user):
    """Test that internal service can read any user's data."""
    headers = make_internal_service_headers()
    response = test_api_function.get(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_regular_user.id


def test_read_user_by_email_requires_admin_or_internal_service(test_api_function, test_user, test_regular_user):
    """Test that regular users cannot look up users by email."""
    headers = make_app_headers_for_user(test_user)
    response = test_api_function.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Admin or internal service access required' in response.json()['detail']


def test_read_user_by_email_requires_internal_service_only(test_api_function, test_admin_user, test_regular_user):
    """Test that admin users can look up users by email."""
    headers = make_app_headers_for_user(test_admin_user)
    response = test_api_function.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_regular_user.email


def test_read_user_by_email_allows_internal_service(test_api_function, test_regular_user):
    """Test that internal service can look up users by email."""
    headers = make_internal_service_headers()
    response = test_api_function.get(f'/users/email/{test_regular_user.email}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['email'] == test_regular_user.email


def test_update_user_requires_own_data_or_admin(test_api_function, test_user, test_regular_user):
    """Test that users can only update their own data unless they're admin."""
    headers = make_app_headers_for_user(test_user)
    update_data = {'name': 'Updated Name'}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only update your own user data' in response.json()['detail']


def test_update_user_allows_own_data(test_api_function, test_regular_user):
    """Test that users can update their own data."""
    headers = make_app_headers_for_user(test_regular_user)
    update_data = {'name': 'Updated Name'}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Updated Name'


def test_update_user_allows_admin(test_api_function, test_admin_user, test_regular_user):
    """Test that admin users can update any user's data."""
    headers = make_app_headers_for_user(test_admin_user)
    update_data = {'name': 'Admin Updated Name'}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Admin Updated Name'


def test_update_user_allows_internal_service(test_api_function, test_regular_user):
    """Test that internal service can update any user's data."""
    headers = make_internal_service_headers()
    update_data = {'name': 'Service Updated Name'}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['name'] == 'Service Updated Name'


def test_delete_user_requires_admin_or_internal_service(test_api_function, test_user, test_regular_user):
    """Test that regular users cannot delete any users."""
    headers = make_app_headers_for_user(test_user)
    response = test_api_function.delete(f'/users/{test_regular_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'Admin access required' in response.json()['detail']


def test_delete_user_prevents_self_deletion(test_api_function, test_admin_user):
    """Test that even admin users cannot delete themselves."""
    headers = make_app_headers_for_user(test_admin_user)
    response = test_api_function.delete(f'/users/{test_admin_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'Cannot delete your own account' in response.json()['detail']


def test_update_user_preferences_requires_own_data_or_admin(test_api_function, test_user, test_regular_user):
    """Test that users can only update their own preferences unless they're admin."""
    headers = make_app_headers_for_user(test_user)
    update_data = {'dark_mode': True}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'can only update your own preferences' in response.json()['detail']


def test_update_user_preferences_allows_own_data(test_api_function, test_regular_user):
    """Test that users can update their own preferences."""
    headers = make_app_headers_for_user(test_regular_user)
    update_data = {'dark_mode': True}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['preferences']['dark_mode'] is True


def test_update_user_preferences_allows_admin(test_api_function, test_admin_user, test_regular_user):
    """Test that admin users can update any user's preferences."""
    headers = make_app_headers_for_user(test_admin_user)
    update_data = {'dark_mode': True}
    response = test_api_function.patch(f'/users/{test_regular_user.id}/preferences/', json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['preferences']['dark_mode'] is True


# =============================================================================
# AUTHENTICATION METHOD TESTS
# =============================================================================


def test_internal_service_auth_invalid_key(test_api_function, test_user):
    """Test that invalid internal service key returns 401."""
    headers = make_invalid_internal_service_headers()
    response = test_api_function.get(f'/users/{test_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Authentication required' in response.json()['detail']


def test_no_authentication_returns_401(test_api_function, test_user):
    """Test that requests without authentication return 401."""
    response = test_api_function.get(f'/users/{test_user.id}/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_jwt_authentication_works(test_api_function, test_user, jwt_handler):
    """Test that JWT authentication works for user endpoints."""
    token = jwt_handler.create_access_token(test_user.get_id())
    headers = make_jwt_header(token)
    response = test_api_function.get(f'/users/{test_user.id}/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data['id'] == test_user.id
