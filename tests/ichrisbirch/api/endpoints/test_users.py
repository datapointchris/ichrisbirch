import pytest
from fastapi import status

import tests.test_data
from ichrisbirch import models
from ichrisbirch import schemas
from tests.helpers import show_status_and_response

TEST_DATA_USERS = tests.test_data.users.BASE_DATA
TEST_DATA_EMAILS = [user.email for user in TEST_DATA_USERS]

NEW_USER = schemas.UserCreate(
    name='Test API Insert User',
    email='test.api.user@openai.com',
    password='stupidP@ssw0rd',
)


@pytest.mark.parametrize('user_id', [1, 2, 3])
def test_read_one_user(test_api, user_id):
    response = test_api.get(f'/users/{user_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_users(test_api):
    response = test_api.get('/users/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_create_user(test_api):
    response = test_api.post('/users/', json=NEW_USER.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_USER.name

    # Test user was created
    response = test_api.get('/users/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 4


@pytest.mark.parametrize('user_id', [1, 2, 3])
def test_delete_user(test_api, user_id):
    endpoint = f'/users/{user_id}/'
    task = test_api.get(endpoint)
    assert task.status_code == status.HTTP_200_OK, show_status_and_response(task)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_user_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a user."""

    # Read all users
    all_users = test_api.get('/users/')
    assert all_users.status_code == status.HTTP_200_OK, show_status_and_response(all_users)
    assert len(all_users.json()) == 3

    # Create new user
    created_user = test_api.post('/users/', json=NEW_USER.model_dump())
    assert created_user.status_code == status.HTTP_201_CREATED, show_status_and_response(created_user)
    assert created_user.json()['name'] == NEW_USER.name

    # Get created task
    user_id = created_user.json().get('id')
    endpoint = f'/users/{user_id}/'
    response_user = test_api.get(endpoint)
    assert response_user.status_code == status.HTTP_200_OK, show_status_and_response(response_user)
    assert response_user.json()['name'] == NEW_USER.name

    # Read all users with new user
    all_users = test_api.get('/users/')
    assert all_users.status_code == status.HTTP_200_OK, show_status_and_response(all_users)
    assert len(all_users.json()) == 4

    # Delete user
    deleted_user = test_api.delete(f'/users/{user_id}/')
    assert deleted_user.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_user)

    # Make sure it's missing
    missing_user = test_api.get(f'/users/{user_id}')
    assert missing_user.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_user)


@pytest.mark.parametrize('email', TEST_DATA_EMAILS)
def test_read_one_user_by_email(test_api, email):
    response = test_api.get(f'/users/email/{email}/')
    user = schemas.User(**response.json())
    assert user.email == email


@pytest.mark.parametrize('user_id', [1, 2, 3])
def test_read_one_user_by_alt_id(test_api, user_id):
    """Since alternative id is assigned by the database, get the user by id then query with alternative id and see if
    they match.
    """
    response = test_api.get(f'/users/{user_id}/')
    id_user = schemas.User(**response.json())
    response = test_api.get(f'/users/alt/{id_user.alternative_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    alt_user = schemas.User(**response.json())
    assert id_user == alt_user


def test_user_set_password():
    user = models.User(**NEW_USER.model_dump())
    # should not be hashed yet, hasn't been inserted in db
    assert user.password == NEW_USER.password
    user.set_password(user.password)  # hash and re-assign to self
    assert user.password != NEW_USER.password
    assert user.check_password(NEW_USER.password)


def test_create_user_password_hashed(test_api):
    created_response = test_api.post('/users/', json=NEW_USER.model_dump())
    assert created_response.status_code == status.HTTP_201_CREATED, show_status_and_response(created_response)
    created_user = models.User(**created_response.json())
    assert created_user.name == NEW_USER.name
    # password should be hashed since it was inserted in the db and not match original
    assert created_user.password != NEW_USER.password
    # but hashing original password should match
    assert created_user.check_password(NEW_USER.password)


@pytest.mark.parametrize('user', TEST_DATA_USERS)
def test_check_user_password_functions(test_api, user):
    """When creating new users, the password should be hashed by the model in the post endpoint and stored in the
    database as the hash.

    Retrieving those passwords and comparing them to the User.check_password output with the original passwords from the
    testing data should be equivalent. Users need to be retrieved by email since id and alternative_id are both assigned
    by the db and not available in the testing data
    """
    response = test_api.get(f'/users/email/{user.email}/')
    db_user = models.User(**response.json())
    assert db_user.check_password(user.password)
