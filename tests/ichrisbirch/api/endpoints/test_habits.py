from datetime import datetime

import pytest
import sqlalchemy
from fastapi import status

import tests.test_data
from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('habitcategories')
    insert_test_data('habits')
    insert_test_data('habitscompleted')
    yield
    delete_test_data('habits')
    delete_test_data('habitscompleted')
    delete_test_data('habitcategories')


class TestHabits:
    ENDPOINT = '/habits/'
    NEW_OBJ = schemas.HabitCreate(
        name='NEW Habit Category ID 2',
        category_id=2,
        is_current=True,
    )
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)

    def test_read_one(self, test_api_logged_in):
        self.crud_tests.test_read_one(test_api_logged_in)

    def test_read_many(self, test_api_logged_in):
        self.crud_tests.test_read_many(test_api_logged_in)

    def test_create(self, test_api_logged_in):
        self.crud_tests.test_create(test_api_logged_in)

    def test_delete(self, test_api_logged_in):
        self.crud_tests.test_delete(test_api_logged_in)

    def test_lifecycle(self, test_api_logged_in):
        self.crud_tests.test_lifecycle(test_api_logged_in)

    def test_read_many_habits_current(self, test_api_logged_in):
        params = {'current': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2

    def test_read_many_habits_not_current(self, test_api_logged_in):
        params = {'current': False}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_hibernate_habit(self, test_api_logged_in):
        first_id = self.crud_tests.item_id_by_position(test_api_logged_in, position=1)
        habit = test_api_logged_in.patch(f'{self.ENDPOINT}{first_id}/', json={'is_current': False})
        assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
        assert habit.json()['is_current'] is False

    def test_revive_habit(self, test_api_logged_in):
        third_id = self.crud_tests.item_id_by_position(test_api_logged_in, position=3)
        habit = test_api_logged_in.patch(f'{self.ENDPOINT}{third_id}/', json={'is_current': True})
        assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
        assert habit.json()['is_current'] is True


class TestHabitCategories:
    ENDPOINT = '/habits/categories/'
    NEW_OBJ = schemas.HabitCategoryCreate(
        name='NEW Category Do Things',
        is_current=True,
    )
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)

    def test_read_one(self, test_api_logged_in):
        self.crud_tests.test_read_one(test_api_logged_in)

    def test_read_many(self, test_api_logged_in):
        self.crud_tests.test_read_many(test_api_logged_in)

    def test_create(self, test_api_logged_in):
        self.crud_tests.test_create(test_api_logged_in)

    def test_delete(self, test_api_logged_in):
        self.crud_tests.test_delete(test_api_logged_in)

    def test_lifecycle(self, test_api_logged_in):
        self.crud_tests.test_lifecycle(test_api_logged_in)

    def test_read_many_categories_current(self, test_api_logged_in):
        params = {'current': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2

    def test_read_many_categories_not_current(self, test_api_logged_in):
        params = {'current': False}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_assign_habit_to_new_category(self, test_api_logged_in):
        created = test_api_logged_in.post(self.ENDPOINT, json=self.NEW_OBJ.model_dump())
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['name'] == self.NEW_OBJ.name

        # Test category was created
        all_obj = test_api_logged_in.get(self.ENDPOINT)
        assert all_obj.status_code == status.HTTP_200_OK, show_status_and_response(all_obj)
        assert len(all_obj.json()) == 4

        # Test can assign new habit to this new category
        new_category_id = created.json()['id']
        modified = self.NEW_OBJ.model_dump().copy()
        modified.update(category_id=new_category_id)
        new_habit = test_api_logged_in.post(TestHabits.ENDPOINT, json=modified)
        assert new_habit.status_code == status.HTTP_201_CREATED, show_status_and_response(new_habit)
        assert new_habit.json()['category_id'] == new_category_id

    def test_hibernate_category(self, test_api_logged_in):
        endpoint = f'{self.ENDPOINT}1/'
        category = test_api_logged_in.patch(endpoint, json={'is_current': False})
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        assert category.json()['is_current'] is False

    def test_revive_category(self, test_api_logged_in):
        endpoint = f'{self.ENDPOINT}3/'
        category = test_api_logged_in.patch(endpoint, json={'is_current': True})
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        assert category.json()['is_current'] is True

    def test_delete_category_in_use_gives_error(self, test_api_logged_in):
        """Test that a category in use cannot be deleted.

        TypeError:
            not all arguments converted during string formatting
        sqlalchemy.exc.PendingRollbackError:
            This Session's transaction has been rolled back due to a previous exception during flush.
        -> This error will be raised, although in the actual API the NotNullConstraint produces
        an IntegrityError which is caught and a 409 response is returned.

        ## Error Code Below ##
        Original exception was:
        (psycopg2.errors.NotNullViolation)
            null value in column "category_id" of relation "habits" violates not-null constraint
        DETAIL:  Failing row contains (1, Habit 1 Category Id 2, null, t).
        [SQL: UPDATE habits.habits SET category_id=%(category_id)s WHERE habits.habits.id = %(habits_habits_id)s]
        [parameters: [{'category_id': None, 'habits_habits_id': 1}, {'category_id': None, 'habits_habits_id': 3}]]
        (Background on this error at: https://sqlalche.me/e/20/gkpj)'),)
        """
        endpoint = f'{self.ENDPOINT}2/'
        category = test_api_logged_in.get(endpoint)
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        with pytest.raises(sqlalchemy.exc.PendingRollbackError):
            # with pytest.raises(TypeError):
            test_api_logged_in.delete(endpoint)


class TestCompletedHabits:
    ENDPOINT = '/habits/completed/'
    NEW_COMPLETED_HABIT = schemas.HabitCompletedCreate(
        name='NEW Completed Habit Category ID 1',
        category_id=1,
        complete_date=datetime(2024, 3, 15),
    )
    TEST_DATA_COMPLETED_HABITS = tests.test_data.habitscompleted.BASE_DATA

    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_COMPLETED_HABIT)

    def test_read_one(self, test_api_logged_in):
        self.crud_tests.test_read_one(test_api_logged_in)

    def test_read_many(self, test_api_logged_in):
        self.crud_tests.test_read_many(test_api_logged_in)

    def test_create(self, test_api_logged_in):
        self.crud_tests.test_create(test_api_logged_in)

    def test_delete(self, test_api_logged_in):
        self.crud_tests.test_delete(test_api_logged_in)

    def test_lifecycle(self, test_api_logged_in):
        self.crud_tests.test_lifecycle(test_api_logged_in)

    def test_read_many_completed_habits_first(self, test_api_logged_in):
        params = {'first': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == self.TEST_DATA_COMPLETED_HABITS[0].name

    def test_read_many_completed_habits_last(self, test_api_logged_in):
        params = {'last': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == self.TEST_DATA_COMPLETED_HABITS[2].name

    def test_read_many_completed_habits_between_dates(self, test_api_logged_in):
        params = {'start_date': '2024-01-01', 'end_date': '2024-01-02'}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2
