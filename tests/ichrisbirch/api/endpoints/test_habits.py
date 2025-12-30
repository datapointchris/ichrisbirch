import datetime as dt

import pytest
import sqlalchemy
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import delete_test_data
from tests.utils.database import insert_test_data

from .crud_test import ApiCrudTester


@pytest.fixture(autouse=True)
def insert_testing_data():
    insert_test_data('habitcategories')  # habits and completed_habits inserted via relationships
    yield
    delete_test_data('habitscompleted', 'habits', 'habitcategories')  # Order matters: children first due to FK


def get_first_category_id(test_api_client):
    """Get the ID of the first category."""
    categories = test_api_client.get('/habits/categories/')
    return categories.json()[0]['id']


def get_current_category(test_api_client):
    """Find a category with is_current=True."""
    categories = test_api_client.get('/habits/categories/')
    for cat in categories.json():
        if cat['is_current']:
            return cat
    raise ValueError('No current category found')


def get_non_current_category(test_api_client):
    """Find a category with is_current=False."""
    categories = test_api_client.get('/habits/categories/')
    for cat in categories.json():
        if not cat['is_current']:
            return cat
    raise ValueError('No non-current category found')


def get_category_with_habits(test_api_client):
    """Find a category that has habits assigned to it."""
    habits = test_api_client.get('/habits/')
    if habits.json():
        category_id = habits.json()[0]['category_id']
        category = test_api_client.get(f'/habits/categories/{category_id}/')
        return category.json()
    raise ValueError('No category with habits found')


def create_habit_crud_tester(category_id: int):
    """Create ApiCrudTester for habits with dynamic category_id."""
    new_obj = schemas.HabitCreate(
        name='NEW Habit Dynamic Category',
        category_id=category_id,
        is_current=True,
    )
    return ApiCrudTester(endpoint='/habits/', new_obj=new_obj)


def create_completed_habit_crud_tester(category_id: int):
    """Create ApiCrudTester for completed habits with dynamic category_id."""
    new_obj = schemas.HabitCompletedCreate(
        name='NEW Completed Habit Dynamic Category',
        category_id=category_id,
        complete_date=dt.datetime(2024, 3, 15),
    )
    return ApiCrudTester(endpoint='/habits/completed/', new_obj=new_obj)


class TestHabits:
    ENDPOINT = '/habits/'

    def test_read_one(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_read_one(test_api_logged_in)

    def test_read_many(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_read_many(test_api_logged_in)

    def test_create(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_create(test_api_logged_in)

    def test_delete(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_delete(test_api_logged_in)

    def test_lifecycle(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_lifecycle(test_api_logged_in)

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
        # Find a current habit to hibernate
        habits = test_api_logged_in.get(self.ENDPOINT, params={'current': True})
        current_habit = habits.json()[0]
        habit_id = current_habit['id']
        habit = test_api_logged_in.patch(f'{self.ENDPOINT}{habit_id}/', json={'is_current': False})
        assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
        assert habit.json()['is_current'] is False

    def test_revive_habit(self, test_api_logged_in):
        # Find a non-current habit to revive
        habits = test_api_logged_in.get(self.ENDPOINT, params={'current': False})
        non_current_habit = habits.json()[0]
        habit_id = non_current_habit['id']
        habit = test_api_logged_in.patch(f'{self.ENDPOINT}{habit_id}/', json={'is_current': True})
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
        # Find a current category to hibernate
        current_cat = get_current_category(test_api_logged_in)
        category_id = current_cat['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
        category = test_api_logged_in.patch(endpoint, json={'is_current': False})
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        assert category.json()['is_current'] is False

    def test_revive_category(self, test_api_logged_in):
        # Find a non-current category to revive
        non_current_cat = get_non_current_category(test_api_logged_in)
        category_id = non_current_cat['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
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
        """
        # Find a category that has habits assigned to it
        cat_with_habits = get_category_with_habits(test_api_logged_in)
        category_id = cat_with_habits['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
        category = test_api_logged_in.get(endpoint)
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        with pytest.raises(sqlalchemy.exc.PendingRollbackError):
            test_api_logged_in.delete(endpoint)


class TestCompletedHabits:
    ENDPOINT = '/habits/completed/'
    # Completed habits sorted by date for first/last queries
    FIRST_COMPLETED_HABIT = 'Completed Habit 1 Category 3'  # 2024-01-01 (earliest)
    LAST_COMPLETED_HABIT = 'Completed Habit 3 Category 2'  # 2024-01-03 (latest)

    def test_read_one(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_read_one(test_api_logged_in)

    def test_read_many(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_read_many(test_api_logged_in)

    def test_create(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_create(test_api_logged_in)

    def test_delete(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_delete(test_api_logged_in)

    def test_lifecycle(self, test_api_logged_in):
        category_id = get_first_category_id(test_api_logged_in)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_lifecycle(test_api_logged_in)

    def test_read_many_completed_habits_first(self, test_api_logged_in):
        params = {'first': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == self.FIRST_COMPLETED_HABIT

    def test_read_many_completed_habits_last(self, test_api_logged_in):
        params = {'last': True}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == self.LAST_COMPLETED_HABIT

    @pytest.mark.parametrize(
        'start_date, end_date, expected_count',
        [
            (dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 2), 2),
            (dt.date(2024, 1, 1), dt.date(2024, 1, 2), 2),
            ('2024-01-01', '2024-01-02', 2),
        ],
    )
    def test_read_many_completed_habits_between_dates(self, test_api_logged_in, start_date, end_date, expected_count):
        params = {'start_date': start_date, 'end_date': end_date}
        response = test_api_logged_in.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == expected_count
