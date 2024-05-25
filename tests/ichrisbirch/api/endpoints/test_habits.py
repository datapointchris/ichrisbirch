from datetime import datetime

import pytest
from fastapi import status

import tests.test_data
import tests.util
from ichrisbirch import schemas
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('habits')


TEST_DATA_COMPLETED_HABITS = tests.test_data.habits.COMPLETED_HABITS

NEW_HABIT = schemas.HabitCreate(
    name='NEW Habit Category ID 2',
    category_id=2,
    is_current=True,
)

NEW_HABIT_CATEGORY = schemas.HabitCategoryCreate(
    name='NEW Category Do Things',
    is_current=True,
)

NEW_COMPLETED_HABIT = schemas.HabitCompletedCreate(
    name='NEW Completed Habit Category ID 1',
    category_id=1,
    complete_date=datetime(2024, 3, 15),
)

# ----------------- HABITS ----------------- #


@pytest.mark.parametrize('habit_id', [1, 2, 3])
def test_read_one_habit(test_api, habit_id):
    response = test_api.get(f'/habits/{habit_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_habits(test_api):
    response = test_api.get('/habits/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_read_many_habits_current(test_api):
    params = {'current': True}
    response = test_api.get('/habits/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_read_many_habits_not_current(test_api):
    params = {'current': False}
    response = test_api.get('/habits/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_create_habit(test_api):
    response = test_api.post('/habits/', json=NEW_HABIT.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert dict(response.json())['name'] == NEW_HABIT.name

    # Test habit was created
    created = test_api.get('/habits/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) == 4


def test_hibernate_habit(test_api):
    endpoint = '/habits/1/'
    habit = test_api.patch(endpoint, json={'is_current': False})
    assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
    assert habit.json()['is_current'] is False


def test_revive_habit(test_api):
    endpoint = '/habits/3/'
    habit = test_api.patch(endpoint, json={'is_current': True})
    assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
    assert habit.json()['is_current'] is True


@pytest.mark.parametrize('habit_id', [1, 2, 3])
def test_delete_habit(test_api, habit_id):
    endpoint = f'/habits/{habit_id}/'
    habit = test_api.get(endpoint)
    assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_habit_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a habit."""

    # Read all habits
    all_habits = test_api.get('/habits/')
    assert all_habits.status_code == status.HTTP_200_OK, show_status_and_response(all_habits)
    assert len(all_habits.json()) == 3

    created_habit = test_api.post('/habits/', json=NEW_HABIT.model_dump())
    assert created_habit.status_code == status.HTTP_201_CREATED, show_status_and_response(created_habit)
    assert created_habit.json()['name'] == NEW_HABIT.name

    # Get created habit
    habit_id = created_habit.json().get('id')
    endpoint = f'/habits/{habit_id}/'
    response_habit = test_api.get(endpoint)
    assert response_habit.status_code == status.HTTP_200_OK, show_status_and_response(response_habit)
    assert response_habit.json()['name'] == NEW_HABIT.name

    # Read all habits with new habit
    all_habits = test_api.get('/habits/')
    assert all_habits.status_code == status.HTTP_200_OK, show_status_and_response(all_habits)
    assert len(all_habits.json()) == 4

    # Delete habit
    deleted_habit = test_api.delete(f'/habits/{habit_id}/')
    assert deleted_habit.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_habit)

    # Make sure it's missing
    missing_habit = test_api.get(f'/habits/{habit_id}')
    assert missing_habit.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_habit)


# ----------------- HABIT CATEGORIES ----------------- #


@pytest.mark.parametrize('category_id', [1, 2, 3])
def test_read_one_category(test_api, category_id):
    response = test_api.get(f'/habits/categories/{category_id}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


def test_read_many_categories(test_api):
    response = test_api.get('/habits/categories/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_read_many_categories_current(test_api):
    params = {'current': True}
    response = test_api.get('/habits/categories/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_read_many_categories_not_current(test_api):
    params = {'current': False}
    response = test_api.get('/habits/categories/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1


def test_create_category(test_api):
    response = test_api.post('/habits/categories/', json=NEW_HABIT_CATEGORY.model_dump())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['name'] == NEW_HABIT_CATEGORY.name

    # Test category was created
    created = test_api.get('/habits/categories/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) == 4

    # Test can assign new habit to this new category
    new_category_id = response.json()['id']
    modified = NEW_HABIT.model_dump().copy()
    modified.update(category_id=new_category_id)
    new_habit = test_api.post('/habits/', json=modified)
    assert new_habit.status_code == status.HTTP_201_CREATED, show_status_and_response(new_habit)
    assert new_habit.json()['category_id'] == new_category_id


def test_hibernate_category(test_api):
    endpoint = '/habits/categories/1/'
    category = test_api.patch(endpoint, json={'is_current': False})
    assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
    assert category.json()['is_current'] is False


def test_revive_category(test_api):
    endpoint = '/habits/categories/3/'
    category = test_api.patch(endpoint, json={'is_current': True})
    assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
    assert category.json()['is_current'] is True


def test_delete_category(test_api):
    endpoint = '/habits/categories/1/'
    category = test_api.get(endpoint)
    assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_delete_category_in_use_gives_error(test_api):
    """Test that a category in use cannot be deleted.

    TypeError: not all arguments converted during string formatting
    -> This error will be raised, although in the actual API the NotNullConstraint produces
    an IntegrityError which is caught and a 409 response is returned.

    ## Error Code Below ##
    Original exception was:
    (psycopg2.errors.NotNullViolation)
        null value in column "category_id" of relation "habits" violates not-null constraint
    DETAIL:  Failing row contains (1, Habit 1 Category Id 2, null, t).
    [SQL: UPDATE habits.habits SET category_id=%(category_id)s WHERE habits.habits.id = %(habits_habits_id)s]
    [parameters: [{\'category_id\': None, \'habits_habits_id\': 1}, {\'category_id\': None, \'habits_habits_id\': 3}]]
    (Background on this error at: https://sqlalche.me/e/20/gkpj)'),)
    """
    endpoint = '/habits/categories/2/'
    category = test_api.get(endpoint)
    assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)

    with pytest.raises(TypeError):
        test_api.delete(endpoint)


def test_category_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a category."""

    # Read all categories
    all_categories = test_api.get('/habits/categories/')
    assert all_categories.status_code == status.HTTP_200_OK, show_status_and_response(all_categories)
    assert len(all_categories.json()) == 3

    created_category = test_api.post('/habits/categories/', json=NEW_HABIT.model_dump())
    assert created_category.status_code == status.HTTP_201_CREATED, show_status_and_response(created_category)
    assert created_category.json()['name'] == NEW_HABIT.name

    # Get created category
    category_id = created_category.json().get('id')
    endpoint = f'/habits/categories/{category_id}/'
    response_category = test_api.get(endpoint)
    assert response_category.status_code == status.HTTP_200_OK, show_status_and_response(response_category)
    assert response_category.json()['name'] == NEW_HABIT.name

    # Read all categories with new category
    all_categories = test_api.get('/habits/categories/')
    assert all_categories.status_code == status.HTTP_200_OK, show_status_and_response(all_categories)
    assert len(all_categories.json()) == 4

    # Delete category
    deleted_category = test_api.delete(f'/habits/categories/{category_id}/')
    assert deleted_category.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted_category)

    # Make sure it's missing
    missing_category = test_api.get(f'/habits/categories/{category_id}')
    assert missing_category.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(missing_category)


# ----------------- COMPLETED HABITS ----------------- #


def test_read_many_completed_habits(test_api):
    response = test_api.get('/habits/completed/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 3


def test_read_many_completed_habits_first(test_api):
    params = {'first': True}
    response = test_api.get('/habits/completed/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == TEST_DATA_COMPLETED_HABITS[0].name


def test_read_many_completed_habits_last(test_api):
    params = {'last': True}
    response = test_api.get('/habits/completed/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == TEST_DATA_COMPLETED_HABITS[2].name


def test_read_many_completed_habits_between_dates(test_api):
    params = {'start_date': '2024-01-01', 'end_date': '2024-01-02'}
    response = test_api.get('/habits/completed/', params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 2


def test_create_completed_habit(test_api):
    response = test_api.post('/habits/completed/', content=NEW_COMPLETED_HABIT.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['name'] == NEW_COMPLETED_HABIT.name

    # Test habit was created
    created = test_api.get('/habits/completed/')
    assert created.status_code == status.HTTP_200_OK, show_status_and_response(created)
    assert len(created.json()) == 4


@pytest.mark.parametrize('habit_id', [1, 2, 3])
def test_delete_completed_habit(test_api, habit_id):
    endpoint = f'/habits/completed/{habit_id}/'
    habit = test_api.get(endpoint)
    assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)

    response = test_api.delete(endpoint)
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

    deleted = test_api.get(endpoint)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(deleted)


def test_completed_habit_lifecycle(test_api):
    """Integration test for CRUD lifecylce of a habit."""

    # Read all habits
    all_completed_habits = test_api.get('/habits/completed/')
    assert all_completed_habits.status_code == status.HTTP_200_OK, show_status_and_response(all_completed_habits)
    assert len(all_completed_habits.json()) == 3

    created_completed_habit = test_api.post('/habits/completed/', content=NEW_COMPLETED_HABIT.model_dump_json())
    assert created_completed_habit.status_code == status.HTTP_201_CREATED, show_status_and_response(
        created_completed_habit
    )
    assert dict(created_completed_habit.json())['name'] == NEW_COMPLETED_HABIT.name

    # Get created habit
    habit_id = created_completed_habit.json().get('id')
    endpoint = f'/habits/completed/{habit_id}/'
    response_completed_habit = test_api.get(endpoint)
    assert response_completed_habit.status_code == status.HTTP_200_OK, show_status_and_response(
        response_completed_habit
    )
    assert dict(response_completed_habit.json())['name'] == NEW_COMPLETED_HABIT.name

    # Read all habits with new habit
    all_completed_habits = test_api.get('/habits/completed/')
    assert all_completed_habits.status_code == status.HTTP_200_OK, show_status_and_response(all_completed_habits)
    assert len(all_completed_habits.json()) == 4

    # Delete habit
    deleted_completed_habit = test_api.delete(f'/habits/completed/{habit_id}/')
    assert deleted_completed_habit.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(
        deleted_completed_habit
    )

    # Make sure it's missing
    missing_completed_habit = test_api.get(f'/habits/completed/{habit_id}')
    assert missing_completed_habit.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(
        missing_completed_habit
    )
