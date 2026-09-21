import datetime as dt
from zoneinfo import ZoneInfo

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
        complete_date=dt.date(2024, 3, 15),
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


class TestCompletedHabitLinksToItsHabit:
    """`habits.completed` carries habit_id alongside the denormalized name.

    Matching a completion to its habit by name breaks on rename: the completion
    stops matching and the habit reads as due again for the rest of the day.
    """

    ENDPOINT = '/habits/completed/'

    def test_completion_round_trips_its_habit_id(self, habit_test_data):
        client = habit_test_data
        habit = client.get('/habits/').json()[0]

        created = client.post(
            self.ENDPOINT,
            json={
                'habit_id': habit['id'],
                'name': habit['name'],
                'category_id': habit['category_id'],
                'complete_date': '2026-07-24',
            },
        )

        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['habit_id'] == habit['id']

    def test_completion_without_a_habit_id_still_records(self, habit_test_data):
        """History predating the column, and completions of a deleted habit."""
        client = habit_test_data
        category_id = get_first_category_id(client)

        created = client.post(
            self.ENDPOINT,
            json={'name': 'Some Historical Habit', 'category_id': category_id, 'complete_date': '2026-07-24'},
        )

        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['habit_id'] is None

    def test_deleting_a_habit_keeps_the_completion(self, habit_test_data):
        """A completion is a historical fact — it outlives the habit it names."""
        client = habit_test_data
        habit = client.get('/habits/').json()[0]
        completion = client.post(
            self.ENDPOINT,
            json={
                'habit_id': habit['id'],
                'name': habit['name'],
                'category_id': habit['category_id'],
                'complete_date': '2026-07-24',
            },
        ).json()

        deleted = client.delete(f'/habits/{habit["id"]}/')
        assert deleted.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT), show_status_and_response(deleted)

        survivor = client.get(f'{self.ENDPOINT}{completion["id"]}/')
        assert survivor.status_code == status.HTTP_200_OK, show_status_and_response(survivor)
        assert survivor.json()['name'] == habit['name'], 'the denormalized name is what makes it survive'
        assert survivor.json()['habit_id'] is None, 'the link clears, the record does not'


class TestCompletedHabitRefusesAFutureDate:
    """A habit cannot be recorded before it has been done.

    Both clients enforce this on the way in, which leaves a third one — a script,
    a scheduler job — with no rule at all. It is checked where the row is written
    so every caller gets the same answer.
    """

    ENDPOINT = '/habits/completed/'

    def _payload(self, category_id: int, complete_date: str) -> dict:
        return {'name': 'Way Ahead Of Myself', 'category_id': category_id, 'complete_date': complete_date}

    def test_a_date_years_out_is_refused(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)

        response = client.post(self.ENDPOINT, json=self._payload(category_id, '2099-01-01'))

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'future' in response.text

    def test_a_past_date_still_records(self, habit_test_data):
        client = habit_test_data
        category_id = get_first_category_id(client)

        response = client.post(self.ENDPOINT, json=self._payload(category_id, '2024-06-01'))

        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    def test_today_in_the_easternmost_zone_records(self, habit_test_data):
        """UTC+14 reaches a day before anywhere else, and it is that client's today."""
        client = habit_test_data
        category_id = get_first_category_id(client)
        kiritimati_today = dt.datetime.now(ZoneInfo('Pacific/Kiritimati')).date()

        response = client.post(self.ENDPOINT, json=self._payload(category_id, kiritimati_today.isoformat()))

        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    def test_the_day_after_the_easternmost_today_is_refused(self, habit_test_data):
        """That day has not begun anywhere, so no client can have done it."""
        client = habit_test_data
        category_id = get_first_category_id(client)
        not_yet = dt.datetime.now(ZoneInfo('Pacific/Kiritimati')).date() + dt.timedelta(days=1)

        response = client.post(self.ENDPOINT, json=self._payload(category_id, not_yet.isoformat()))

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


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

    def test_first_and_last_still_answer_with_one_under_a_wider_limit(self, habit_test_data):
        """`first` is a cap of one, so a limit above it cannot widen the answer."""
        client = habit_test_data
        for selector in ('first', 'last'):
            response = client.get(self.ENDPOINT, params={selector: True, 'limit': 50})
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
            assert len(response.json()) == 1, f'{selector} widened to {len(response.json())} rows'

    def test_zero_outranks_first_and_last(self, habit_test_data):
        """Zero is a row count a caller can mean, and it is tighter than one."""
        client = habit_test_data
        for selector in ('first', 'last'):
            response = client.get(self.ENDPOINT, params={selector: True, 'limit': 0})
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
            assert response.json() == [], f'{selector} answered a zero limit with rows'

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

    @pytest.mark.parametrize(
        'params, expected_count',
        [
            ({'start_date': '2024-01-02'}, 2),
            ({'end_date': '2024-01-02'}, 2),
            ({}, 3),
        ],
    )
    def test_read_many_completed_habits_one_bound_is_open_ended(self, txn_api_logged_in, params, expected_count):
        """One bound narrows on its own; a half-specified range never widens to everything."""
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'habitcategories')
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
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'not-a-date' in response.json()['detail'], 'the error must name the value that was rejected'

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


class TestHabitsDay:
    """The day's board, composed server-side.

    The split it performs is unit-tested against the service beside it. These
    cases are about the endpoint: which day it resolves, how it refuses a zone it
    cannot read, and that the three fields agree with each other.
    """

    ENDPOINT = '/habits/day/'

    def _complete(self, client, habit: dict, day: dt.date):
        payload = {
            'habit_id': habit['id'],
            'name': habit['name'],
            'category_id': habit['category_id'],
            'complete_date': day.isoformat(),
        }
        response = client.post('/habits/completed/', json=payload)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)

    def test_an_untouched_day_has_every_current_habit_due(self, habit_test_data):
        client = habit_test_data

        response = client.get(self.ENDPOINT, params={'date': '2020-01-01', 'timezone': 'America/New_York'})

        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        day = response.json()
        assert day['completed'] == []
        assert len(day['due']) == day['current_total']
        assert day['current_total'] > 0, 'the seed gives this nothing to report'

    def test_a_completion_moves_its_habit_out_of_due(self, habit_test_data):
        client = habit_test_data
        current = [h for h in client.get('/habits/', params={'current': True}).json()]
        target = current[0]
        self._complete(client, target, dt.date(2020, 1, 1))

        day = client.get(self.ENDPOINT, params={'date': '2020-01-01', 'timezone': 'UTC'}).json()

        assert [c['habit_id'] for c in day['completed']] == [target['id']]
        assert target['id'] not in [h['id'] for h in day['due']]
        assert len(day['due']) + 1 == day['current_total']

    def test_a_completion_stays_on_its_day_in_every_zone(self, habit_test_data):
        """A completion holds the day it was done, not a moment a zone can move.

        Stored as a moment, 21:00 in New York on the 1st read as the 2nd from any
        zone east of UTC, so the board depended on where it was read from.
        """
        client = habit_test_data
        target = client.get('/habits/', params={'current': True}).json()[0]
        self._complete(client, target, dt.date(2020, 1, 1))

        for zone in ('America/New_York', 'UTC', 'Pacific/Auckland'):
            day = client.get(self.ENDPOINT, params={'date': '2020-01-01', 'timezone': zone}).json()
            assert [c['habit_id'] for c in day['completed']] == [target['id']], zone

    def test_the_response_echoes_the_day_it_resolved(self, habit_test_data):
        client = habit_test_data

        day = client.get(self.ENDPOINT, params={'date': '2020-01-01', 'timezone': 'America/New_York'}).json()

        assert day['date'] == '2020-01-01'
        assert day['timezone'] == 'America/New_York'

    def test_an_absent_date_is_today_in_the_given_zone(self, habit_test_data):
        """The caller sends its zone and the server names the day, so a client
        that computes its own today cannot disagree with the split."""
        client = habit_test_data

        day = client.get(self.ENDPOINT, params={'timezone': 'Pacific/Kiritimati'}).json()

        expected = dt.datetime.now(dt.UTC).astimezone(ZoneInfo('Pacific/Kiritimati')).date()
        assert day['date'] == expected.isoformat()

    def test_an_absent_timezone_is_utc(self, habit_test_data):
        client = habit_test_data

        day = client.get(self.ENDPOINT).json()

        assert day['timezone'] == 'UTC'
        assert day['date'] == dt.datetime.now(dt.UTC).date().isoformat()

    def test_a_zone_that_is_not_an_iana_name_is_a_422(self, habit_test_data):
        """Refused by name rather than silently falling back to UTC, which would
        answer the wrong day and look like a working response."""
        client = habit_test_data

        response = client.get(self.ENDPOINT, params={'timezone': 'Not/AZone'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'Not/AZone' in response.text

    def test_a_malformed_date_is_a_422(self, habit_test_data):
        client = habit_test_data

        response = client.get(self.ENDPOINT, params={'date': 'the 3rd'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_a_hibernating_habit_is_not_on_the_board(self, habit_test_data):
        """`current_total` counts what you are tracking, so a hibernating habit is
        neither due nor part of the denominator."""
        client = habit_test_data
        hibernating = client.get('/habits/', params={'current': False}).json()
        assert hibernating, 'the seed gives this nothing to exclude'

        day = client.get(self.ENDPOINT, params={'date': '2020-01-01'}).json()

        board = {h['id'] for h in day['due']}
        assert board.isdisjoint({h['id'] for h in hibernating})

    def test_the_board_is_ordered_by_habit_id(self, habit_test_data):
        client = habit_test_data

        day = client.get(self.ENDPOINT, params={'date': '2020-01-01'}).json()

        ids = [h['id'] for h in day['due']]
        assert ids == sorted(ids)

    def test_completions_carrying_no_habit_id_come_back_newest_first(self, habit_test_data):
        """Every one of them ties on the sort key, so the query has to break it."""
        client = habit_test_data
        category_id = client.get('/habits/categories/').json()[0]['id']
        for name in ('earliest', 'middle', 'latest'):
            payload = {'name': name, 'category_id': category_id, 'complete_date': '2020-01-01'}
            created = client.post('/habits/completed/', json=payload)
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)

        day = client.get(self.ENDPOINT, params={'date': '2020-01-01', 'timezone': 'UTC'}).json()

        orphans = [c['name'] for c in day['completed'] if c['habit_id'] is None]
        assert orphans == ['latest', 'middle', 'earliest']
