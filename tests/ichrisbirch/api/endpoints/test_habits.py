import datetime as dt

import pytest
import sqlalchemy
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester


@pytest.fixture
def habit_test_data(txn_api_logged_in):
    """Provide transactional test data for habit tests."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'habitcategories')  # habits and completed_habits inserted via relationships
    return client


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

    def test_read_one(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_read_one(client)

    def test_read_many(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_read_many(client)

    def test_create(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_create(client)

    def test_delete(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_delete(client)

    def test_lifecycle(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_habit_crud_tester(category_id)
        crud_tester.test_lifecycle(client)

    def test_read_many_habits_current(self, habit_test_data):
        client = habit_test_data
        params = {'current': True}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2

    def test_read_many_habits_not_current(self, habit_test_data):
        client = habit_test_data
        params = {'current': False}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_hibernate_habit(self, habit_test_data):
        client = habit_test_data
        # Find a current habit to hibernate
        habits = client.get(self.ENDPOINT, params={'current': True})
        current_habit = habits.json()[0]
        habit_id = current_habit['id']
        habit = client.patch(f'{self.ENDPOINT}{habit_id}/', json={'is_current': False})
        assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
        assert habit.json()['is_current'] is False

    def test_revive_habit(self, habit_test_data):
        client = habit_test_data
        # Find a non-current habit to revive
        habits = client.get(self.ENDPOINT, params={'current': False})
        non_current_habit = habits.json()[0]
        habit_id = non_current_habit['id']
        habit = client.patch(f'{self.ENDPOINT}{habit_id}/', json={'is_current': True})
        assert habit.status_code == status.HTTP_200_OK, show_status_and_response(habit)
        assert habit.json()['is_current'] is True


class TestHabitCategories:
    ENDPOINT = '/habits/categories/'
    NEW_OBJ = schemas.HabitCategoryCreate(
        name='NEW Category Do Things',
        is_current=True,
    )
    crud_tests = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ)

    def test_read_one(self, habit_test_data):
        client = habit_test_data
        self.crud_tests.test_read_one(client)

    def test_read_many(self, habit_test_data):
        client = habit_test_data
        self.crud_tests.test_read_many(client)

    def test_create(self, habit_test_data):
        client = habit_test_data
        self.crud_tests.test_create(client)

    def test_delete(self, habit_test_data):
        client = habit_test_data
        self.crud_tests.test_delete(client)

    def test_lifecycle(self, habit_test_data):
        client = habit_test_data
        self.crud_tests.test_lifecycle(client)

    def test_read_many_categories_current(self, habit_test_data):
        client = habit_test_data
        params = {'current': True}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2

    def test_read_many_categories_not_current(self, habit_test_data):
        client = habit_test_data
        params = {'current': False}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_assign_habit_to_new_category(self, habit_test_data):
        client = habit_test_data
        created = client.post(self.ENDPOINT, json=self.NEW_OBJ.model_dump())
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['name'] == self.NEW_OBJ.name

        # Test category was created
        all_obj = client.get(self.ENDPOINT)
        assert all_obj.status_code == status.HTTP_200_OK, show_status_and_response(all_obj)
        assert len(all_obj.json()) == 4

        # Test can assign new habit to this new category
        new_category_id = created.json()['id']
        modified = self.NEW_OBJ.model_dump().copy()
        modified.update(category_id=new_category_id)
        new_habit = client.post(TestHabits.ENDPOINT, json=modified)
        assert new_habit.status_code == status.HTTP_201_CREATED, show_status_and_response(new_habit)
        assert new_habit.json()['category_id'] == new_category_id

    def test_hibernate_category(self, habit_test_data):
        client = habit_test_data
        # Find a current category to hibernate
        current_cat = get_current_category(client)
        category_id = current_cat['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
        category = client.patch(endpoint, json={'is_current': False})
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        assert category.json()['is_current'] is False

    def test_revive_category(self, habit_test_data):
        client = habit_test_data
        # Find a non-current category to revive
        non_current_cat = get_non_current_category(client)
        category_id = non_current_cat['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
        category = client.patch(endpoint, json={'is_current': True})
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        assert category.json()['is_current'] is True

    def test_delete_category_in_use_gives_error(self, habit_test_data):
        """Test that a category in use cannot be deleted.

        TypeError:
            not all arguments converted during string formatting
        sqlalchemy.exc.PendingRollbackError:
            This Session's transaction has been rolled back due to a previous exception during flush.
        -> This error will be raised, although in the actual API the NotNullConstraint produces
        an IntegrityError which is caught and a 409 response is returned.
        """
        client = habit_test_data
        # Find a category that has habits assigned to it
        cat_with_habits = get_category_with_habits(client)
        category_id = cat_with_habits['id']
        endpoint = f'{self.ENDPOINT}{category_id}/'
        category = client.get(endpoint)
        assert category.status_code == status.HTTP_200_OK, show_status_and_response(category)
        with pytest.raises(sqlalchemy.exc.PendingRollbackError):
            client.delete(endpoint)


class TestCompletedHabits:
    ENDPOINT = '/habits/completed/'
    # Completed habits sorted by date for first/last queries
    FIRST_COMPLETED_HABIT = 'Completed Habit 1 Category 3'  # 2024-01-01 (earliest)
    LAST_COMPLETED_HABIT = 'Completed Habit 3 Category 2'  # 2024-01-03 (latest)

    def test_read_one(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_read_one(client)

    def test_read_many(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_read_many(client)

    def test_create(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_create(client)

    def test_delete(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_delete(client)

    def test_lifecycle(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)
        crud_tester = create_completed_habit_crud_tester(category_id)
        crud_tester.test_lifecycle(client)

    def test_read_many_completed_habits_first(self, habit_test_data):
        client = habit_test_data
        params = {'first': True}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == self.FIRST_COMPLETED_HABIT

    def test_read_many_completed_habits_last(self, habit_test_data):
        client = habit_test_data
        params = {'last': True}
        response = client.get(self.ENDPOINT, params=params)
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
    def test_read_many_completed_habits_between_dates(self, txn_api_logged_in, start_date, end_date, expected_count):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'habitcategories')
        params = {'start_date': start_date, 'end_date': end_date}
        response = client.get(self.ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == expected_count


class TestHabitsQueryParameters:
    """Test query parameter filtering on habits endpoints.

    Test data (from tests/test_data/habitcategories.py):
    - 3 categories: 2 current (Category 1, 2), 1 not current (Category 3)
    - 3 habits: 2 current (in Cat 2 and Cat 3), 1 not current (in Cat 2)
    - 3 completed habits with dates: 2024-01-01, 2024-01-02, 2024-01-03
    """

    HABITS_ENDPOINT = '/habits/'
    CATEGORIES_ENDPOINT = '/habits/categories/'
    COMPLETED_ENDPOINT = '/habits/completed/'

    def test_habits_limit_parameter(self, habit_test_data):
        """Test that limit parameter works correctly."""
        client = habit_test_data
        # Get all habits first to know the total count
        all_response = client.get(self.HABITS_ENDPOINT)
        assert all_response.status_code == status.HTTP_200_OK
        total_habits = len(all_response.json())
        assert total_habits >= 2, 'Need at least 2 habits for limit test'

        # Test limit=1
        response = client.get(self.HABITS_ENDPOINT, params={'limit': 1})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_habits_limit_with_current_filter(self, habit_test_data):
        """Test limit combined with current filter.

        BUG: If limit is applied before filter, we may get fewer results than expected.
        With test data: 2 current habits, 1 not current.
        Requesting limit=2&current=True should return 2 habits.
        """
        client = habit_test_data
        # First verify we have 2 current habits
        current_response = client.get(self.HABITS_ENDPOINT, params={'current': True})
        assert len(current_response.json()) == 2, 'Test data should have 2 current habits'

        # Now test limit=2 with current=True - should still get 2
        response = client.get(self.HABITS_ENDPOINT, params={'limit': 2, 'current': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        # If bug exists (limit before filter), this might return < 2
        assert len(response.json()) == 2, 'limit should be applied AFTER filtering'

    def test_categories_limit_parameter(self, habit_test_data):
        """Test that limit parameter works on categories."""
        client = habit_test_data
        response = client.get(self.CATEGORIES_ENDPOINT, params={'limit': 1})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 1

    def test_categories_limit_with_current_filter(self, habit_test_data):
        """Test limit combined with current filter on categories.

        BUG: Same issue as habits - limit before filter.
        With test data: 2 current categories, 1 not current.
        """
        client = habit_test_data
        # First verify we have 2 current categories
        current_response = client.get(self.CATEGORIES_ENDPOINT, params={'current': True})
        assert len(current_response.json()) == 2, 'Test data should have 2 current categories'

        # Now test limit=2 with current=True - should still get 2
        response = client.get(self.CATEGORIES_ENDPOINT, params={'limit': 2, 'current': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 2, 'limit should be applied AFTER filtering'

    def test_completed_invalid_date_format(self, habit_test_data):
        """Test that invalid date formats return 422 Unprocessable Entity."""
        client = habit_test_data
        response = client.get(
            self.COMPLETED_ENDPOINT,
            params={
                'start_date': 'not-a-date',
                'end_date': '2024-01-02',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, show_status_and_response(response)
        assert 'Invalid date format' in response.json()['detail']

    def test_habits_not_found_returns_404(self, habit_test_data):
        """Test that non-existent habit returns 404."""
        client = habit_test_data
        response = client.get(f'{self.HABITS_ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_categories_not_found_returns_404(self, habit_test_data):
        """Test that non-existent category returns 404."""
        client = habit_test_data
        response = client.get(f'{self.CATEGORIES_ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_completed_not_found_returns_404(self, habit_test_data):
        """Test that non-existent completed habit returns 404."""
        client = habit_test_data
        response = client.get(f'{self.COMPLETED_ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
