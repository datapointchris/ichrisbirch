import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

NEW_OBJ = schemas.EventCreate(
    name='Event 4',
    date=dt.datetime(2022, 10, 4, 20),
    venue='Venue 4',
    url='https://example.com/event4',
    cost=40.0,
    attending=False,
    notes='Notes for Event 4',
)

ENDPOINT = '/events'


@pytest.fixture
def event_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'events')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, list_params={'when': 'all'})
    return client, crud_tester


def test_read_one(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_read_many(client)


def test_create(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_create(client)


def test_delete(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(event_crud_tester):
    client, crud_tester = event_crud_tester
    crud_tester.test_lifecycle(client)


# The reading on the clock at the venue is what is stored, whatever shape it arrives
# in. An offset describes the same wall time, so it is dropped rather than converted —
# converting would display a 19:00 event as 15:00 four hours west.
@pytest.mark.parametrize(
    ['event_date', 'output'],
    [
        (dt.datetime(2022, 10, 4), '2022-10-04T00:00:00'),
        (dt.datetime(2022, 10, 4, 12), '2022-10-04T12:00:00'),
        (dt.datetime(2022, 10, 4, 12, tzinfo=ZoneInfo('America/Chicago')), '2022-10-04T12:00:00'),
        ('2022-10-04', '2022-10-04T00:00:00'),
        ('2022-10-04T12:00:00', '2022-10-04T12:00:00'),
        ('2022-10-04T12:00:00-05:00', '2022-10-04T12:00:00'),
    ],
)
def test_create_event_date_formats(txn_api_logged_in, event_date, output):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'events')
    event_obj = schemas.EventCreate(
        name='Event Date Test',
        date=event_date,
        venue='Test Venue',
        url='https://example.com/test',
        cost=10.0,
        attending=False,
        notes='Date format test',
    )
    response = client.post(ENDPOINT, json=event_obj.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    event = client.get(f'{ENDPOINT}/{response.json()["id"]}')
    assert event.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert event.json()['date'] == output


def test_attend_event(event_crud_tester):
    """Test marking an event as attending."""
    client, crud_tester = event_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Mark as attending
    response = client.patch(f'{ENDPOINT}/{first_id}/attend')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['attending'] is True

    # Verify persistence
    response = client.get(f'{ENDPOINT}/{first_id}')
    assert response.json()['attending'] is True


def test_partial_update(event_crud_tester):
    """Test partial update with only some fields."""
    client, crud_tester = event_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)

    # Get original event
    original = client.get(f'{ENDPOINT}/{first_id}').json()

    # Update only venue
    response = client.patch(f'{ENDPOINT}/{first_id}', json={'venue': 'Updated Venue'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    updated = response.json()
    assert updated['venue'] == 'Updated Venue'
    assert updated['name'] == original['name']  # Other fields unchanged


class TestEventsNotFound:
    """Test 404 responses for non-existent events."""

    def test_read_one_not_found(self, event_crud_tester):
        """GET /{id} returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.get(f'{ENDPOINT}/99999')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, event_crud_tester):
        """DELETE /{id} returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.delete(f'{ENDPOINT}/99999')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, event_crud_tester):
        """PATCH /{id} returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.patch(f'{ENDPOINT}/99999', json={'name': 'Does Not Exist'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_attend_not_found(self, event_crud_tester):
        """PATCH /{id}/attend returns 404 for non-existent event."""
        client, _ = event_crud_tester
        response = client.patch(f'{ENDPOINT}/99999/attend')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)


class TestEventWallClock:
    """The date is a reading on a clock at the venue, and timezone resolves it.

    Storing an instant makes the reading depend on who is looking: a 19:00 event
    entered on a machine four hours west of UTC comes back as 15:00.
    """

    def test_a_non_utc_event_round_trips_its_zone(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        payload = {
            'name': 'Tokyo Show',
            'date': '2026-09-28T19:00:00',
            'timezone': 'Asia/Tokyo',
            'venue': 'Budokan',
            'cost': 0.0,
            'attending': True,
        }

        created = client.post(ENDPOINT, json=payload)

        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        body = created.json()
        assert body['date'] == '2026-09-28T19:00:00', 'the reading is stored, not an instant'
        assert body['timezone'] == 'Asia/Tokyo'

    def test_an_offset_on_the_date_is_dropped_not_converted(self, txn_api_logged_in):
        """An offset describes the same reading, so the reading survives it."""
        client, session = txn_api_logged_in
        payload = {
            'name': 'Offset Sent',
            'date': '2026-09-28T19:00:00-04:00',
            'timezone': 'America/New_York',
            'venue': 'Hall',
            'cost': 0.0,
            'attending': False,
        }

        created = client.post(ENDPOINT, json=payload)

        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['date'] == '2026-09-28T19:00:00'

    def test_an_offset_is_refused_as_a_timezone(self, txn_api_logged_in):
        """An offset cannot say what the local time will be on a future date."""
        client, session = txn_api_logged_in
        payload = {
            'name': 'Bad Zone',
            'date': '2026-09-28T19:00:00',
            'timezone': '-04:00',
            'venue': 'Hall',
            'cost': 0.0,
            'attending': False,
        }

        response = client.post(ENDPOINT, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'IANA' in response.text

    def test_an_explicit_null_timezone_is_a_422_not_a_500(self, txn_api_logged_in):
        """exclude_unset covers the omitted case, so a null can only be deliberate."""
        client, session = txn_api_logged_in
        created = client.post(
            ENDPOINT,
            json={
                'name': 'Nullable',
                'date': '2026-09-28T19:00:00',
                'timezone': 'UTC',
                'venue': 'Hall',
                'cost': 0.0,
                'attending': False,
            },
        )
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)

        response = client.patch(f'{ENDPOINT}/{created.json()["id"]}', json={'timezone': None})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_omitted_timezone_leaves_it_unchanged(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        created = client.post(
            ENDPOINT,
            json={
                'name': 'Unchanged',
                'date': '2026-09-28T19:00:00',
                'timezone': 'Asia/Tokyo',
                'venue': 'Hall',
                'cost': 0.0,
                'attending': False,
            },
        )
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)

        updated = client.patch(f'{ENDPOINT}/{created.json()["id"]}', json={'name': 'Renamed'})

        assert updated.status_code == status.HTTP_200_OK, show_status_and_response(updated)
        assert updated.json()['timezone'] == 'Asia/Tokyo'

    def test_listing_orders_by_the_resolved_instant_not_the_reading(self, txn_api_logged_in):
        """09:00 in Tokyo is thirteen hours before 08:00 in New York."""
        client, session = txn_api_logged_in
        for name, zone, reading in [
            ('New York morning', 'America/New_York', '2026-09-28T08:00:00'),
            ('Tokyo morning', 'Asia/Tokyo', '2026-09-28T09:00:00'),
        ]:
            created = client.post(
                ENDPOINT,
                json={'name': name, 'date': reading, 'timezone': zone, 'venue': 'V', 'cost': 0.0, 'attending': False},
            )
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)

        listed = client.get(ENDPOINT, params={'when': 'all'})

        assert listed.status_code == status.HTTP_200_OK, show_status_and_response(listed)
        names = [e['name'] for e in listed.json() if e['name'].endswith('morning')]
        assert names == ['Tokyo morning', 'New York morning']


def create_event(client, name: str, reading: dt.datetime, zone: str) -> None:
    payload = {'name': name, 'date': reading.isoformat(), 'timezone': zone, 'venue': 'V', 'cost': 0.0, 'attending': False}
    created = client.post(ENDPOINT, json=payload)
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)


def listed_names(client, **params) -> list[str]:
    response = client.get(ENDPOINT, params=params)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    return [event['name'] for event in response.json()]


def start_of_today(zone: str) -> dt.datetime:
    return dt.datetime.combine(dt.datetime.now(ZoneInfo(zone)).date(), dt.time.min, tzinfo=ZoneInfo(zone))


class TestEventScope:
    """`when` picks upcoming, past or all, with today read in the request's zone.

    Past events pile up forever and upcoming ones stay a handful, so the
    collection read defaults to upcoming and a caller wanting history asks for it.
    """

    @pytest.fixture
    def client_with_both_sides_of_today(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        opens = start_of_today('UTC').replace(tzinfo=None)
        create_event(client, 'last month', opens - dt.timedelta(days=30), 'UTC')
        create_event(client, 'last night', opens - dt.timedelta(minutes=30), 'UTC')
        create_event(client, 'first thing today', opens + dt.timedelta(minutes=30), 'UTC')
        create_event(client, 'next month', opens + dt.timedelta(days=30), 'UTC')
        return client

    def test_the_default_is_today_onward_soonest_first(self, client_with_both_sides_of_today):
        """An event earlier today has not dropped off; it is still today's."""
        names = listed_names(client_with_both_sides_of_today, timezone='UTC')
        assert names == ['first thing today', 'next month']

    def test_past_is_before_today_most_recent_first(self, client_with_both_sides_of_today):
        """Most recent first, so a limit takes the latest rather than the oldest."""
        names = listed_names(client_with_both_sides_of_today, when='past', timezone='UTC')
        assert names == ['last night', 'last month']

    def test_a_limit_on_past_takes_the_most_recent(self, client_with_both_sides_of_today):
        names = listed_names(client_with_both_sides_of_today, when='past', timezone='UTC', limit=1)
        assert names == ['last night']

    def test_all_is_every_event_in_date_order(self, client_with_both_sides_of_today):
        names = listed_names(client_with_both_sides_of_today, when='all', timezone='UTC')
        assert names == ['last month', 'last night', 'first thing today', 'next month']

    def test_an_unknown_scope_is_a_422(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        response = client.get(ENDPOINT, params={'when': 'soon'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_today_is_read_in_the_request_zone(self, txn_api_logged_in):
        """One instant falls on today in one zone and before today in another.

        UTC and Kolkata are five and a half hours apart, so their midnights never
        coincide, and an event between them is upcoming in the zone whose day
        opened first and past in the other.
        """
        client, _ = txn_api_logged_in
        utc_opens, kolkata_opens = start_of_today('UTC'), start_of_today('Asia/Kolkata')
        earlier, later = sorted([(utc_opens, 'UTC'), (kolkata_opens, 'Asia/Kolkata')])
        between = earlier[0] + (later[0] - earlier[0]) / 2
        create_event(client, 'between midnights', between.astimezone(dt.UTC).replace(tzinfo=None), 'UTC')

        assert 'between midnights' in listed_names(client, timezone=earlier[1])
        assert 'between midnights' in listed_names(client, when='past', timezone=later[1])

    def test_an_event_resolves_in_its_own_zone_before_it_is_compared(self, txn_api_logged_in):
        """A Honolulu reading of 23:30 on UTC's yesterday is 09:30 UTC today, so it is upcoming.

        Comparing the reading as written would put it before UTC's midnight.
        """
        client, _ = txn_api_logged_in
        yesterday_late = start_of_today('UTC').replace(tzinfo=None) - dt.timedelta(minutes=30)
        create_event(client, 'read at the venue', yesterday_late, 'Pacific/Honolulu')

        assert 'read at the venue' in listed_names(client, timezone='UTC')
