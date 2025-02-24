import pytest
from fastapi import status
from sqlalchemy import select

import tests.test_data
import tests.util
from ichrisbirch import models
from ichrisbirch import schemas
from tests.ichrisbirch.api.endpoints.test_auth import make_app_headers_for_user
from tests.ichrisbirch.api.endpoints.test_auth import make_jwt_header
from tests.util import show_status_and_response

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')
    yield
    tests.util.delete_test_data('users')


TEST_DATA_USERS = tests.test_data.users.BASE_DATA
TEST_DATA_EMAILS = [user.email for user in TEST_DATA_USERS]
ENDPOINT = '/users/'
NEW_OBJ = schemas.UserCreate(
    name='Test API Insert User',
    email='test.api.user@openai.com',
    password='stupidP@ssw0rd',
)


@pytest.fixture()
def test_user():
    # look in tests.test_data.users to see user
    with tests.util.SessionTesting() as session:
        return session.execute(select(models.User).where(models.User.email == 'regular_user_1@gmail.com')).scalar()


crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)


def test_read_one(test_api_logged_in):
    crud_tests.test_read_one(test_api_logged_in)


def test_read_many(test_api_logged_in):
    crud_tests.test_read_many(test_api_logged_in)


def test_create(test_api_logged_in):
    crud_tests.test_create(test_api_logged_in)


def test_delete(test_api_logged_in):
    crud_tests.test_delete(test_api_logged_in)


@pytest.mark.skip(reason='An extra user is inserted for login, which changes length in users table, 3 => 4')
def test_lifecycle(test_api_logged_in):
    crud_tests.test_lifecycle(test_api_logged_in)


def test_patch_user(test_api_logged_in):
    first_user_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    new_name = 'Updated User 1 Name'
    response = test_api_logged_in.patch(f'{ENDPOINT}{first_user_id}/', json={'name': new_name})
    assert response.json()['name'] == new_name


@pytest.mark.parametrize('email', TEST_DATA_EMAILS)
def test_read_one_user_by_email(test_api_logged_in, email):
    response = test_api_logged_in.get(f'/users/email/{email}/')
    user = schemas.User(**response.json())
    assert user.email == email


def test_read_one_user_by_alt_id(test_api_logged_in):
    """Since alternative id is assigned by the database, get the user by id then query with alternative id and see if
    they match.
    """
    first_id = crud_tests.item_id_by_position(test_api_logged_in, position=1)
    response = test_api_logged_in.get(f'/users/{first_id}/')
    id_user = schemas.User(**response.json())
    response = test_api_logged_in.get(f'/users/alt/{id_user.alternative_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    alt_user = schemas.User(**response.json())
    assert id_user == alt_user


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
def test_check_user_password_functions(test_api_logged_in, user):
    """When creating new users, the password should be hashed by the model in the post endpoint and stored in the
    database as the hash.

    Retrieving those passwords and comparing them to the User.check_password output with the original passwords from the
    testing data should be equivalent. Users need to be retrieved by email since id and alternative_id are both assigned
    by the db and not available in the testing data
    """
    response = test_api_logged_in.get(f'/users/email/{user.email}/')
    db_user = models.User(**response.json())
    assert db_user.check_password(user.password)


def test_get_user_me_application_headers(test_api_function, test_user):
    headers = make_app_headers_for_user(test_user)
    response = test_api_function.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_user.name


def test_get_user_me_jwt(test_api_function, test_user):
    """Send a request to /auth/token/ to get a token using oauth2 username and password.

    Then use the token to get /me/ endpoint
    """
    data = {'username': test_user.email, 'password': 'regular_user_1_password'}
    response = test_api_function.post('/auth/token/', data=data)
    token = response.json()['access_token']
    headers = make_jwt_header(token)
    response = test_api_function.get('/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == test_user.name
