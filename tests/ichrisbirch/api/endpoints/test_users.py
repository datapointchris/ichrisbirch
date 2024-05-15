import pytest
from fastapi import status

import tests.test_data
from ichrisbirch import schemas
from tests.helpers import show_status_and_response

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
    task_id = created_user.json().get('id')
    endpoint = f'/users/{task_id}/'
    response_user = test_api.get(endpoint)
    assert response_user.status_code == status.HTTP_200_OK, show_status_and_response(response_user)
    assert response_user.json()['name'] == NEW_USER.name

    # Read all users with new user
    all_users = test_api.get('/users/')
    assert all_users.status_code == status.HTTP_200_OK, show_status_and_response(all_users)
    assert len(all_users.json()) == 4

    # Delete Autotask
    deleted_user = test_api.delete(f'/users/{task_id}/')
    assert deleted_user.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_user)

    # Make sure it's missing
    missing_user = test_api.get(f'/users/{task_id}')
    assert missing_user.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_user)


emails = [user.email for user in tests.test_data.users.BASE_DATA]


@pytest.mark.parametrize('email', emails)
def test_read_one_user_by_email(test_api, email):
    response = test_api.get(f'/users/email/{email}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


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
