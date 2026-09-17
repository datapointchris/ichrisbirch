import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/strains/'
NEW_OBJ = schemas.StrainCreate(
    name='Wedding Cake',
    breeder='Seed Junky Genetics',
    lineage='Triangle Kush x Animal Mints',
    strain_type='indica_dominant',
    status='tried',
    thc_percent=25.0,
    rating=8,
    effects=['relaxed', 'euphoric'],
    flavors=['vanilla', 'sweet'],
    terpenes=['limonene'],
    tags=['nighttime'],
    notes='Strong. A little goes a long way.',
)


@pytest.fixture
def strain_crud_tester(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'strains')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='name')
    return client, crud_tester


def test_read_one(strain_crud_tester):
    client, crud_tester = strain_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(strain_crud_tester):
    client, crud_tester = strain_crud_tester
    crud_tester.test_read_many(client)


def test_create(strain_crud_tester):
    client, crud_tester = strain_crud_tester
    crud_tester.test_create(client)


def test_delete(strain_crud_tester):
    client, crud_tester = strain_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(strain_crud_tester):
    client, crud_tester = strain_crud_tester
    crud_tester.test_lifecycle(client)


def test_a_strain_needs_only_a_name(strain_crud_tester):
    """Almost every column is nullable, because a label carries what it carries."""
    client, _ = strain_crud_tester
    response = client.post(ENDPOINT, json={'name': 'MAC 1'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    data = response.json()
    assert data['status'] == 'want_to_try', 'A strain nobody has tried is the default'
    assert data['strain_type'] is None
    assert data['rating'] is None


def test_an_unnamed_array_reads_back_as_empty_rather_than_null(strain_crud_tester):
    """The columns are NOT NULL DEFAULT '{}', so a client never branches on null."""
    client, _ = strain_crud_tester
    created = client.post(ENDPOINT, json={'name': 'Runtz 2'})
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    data = created.json()
    assert data['effects'] == []
    assert data['flavors'] == []
    assert data['terpenes'] == []
    assert data['tags'] == []


def test_an_explicit_null_array_is_stored_as_empty(strain_crud_tester):
    """A null would reach a NOT NULL column and fail the insert, so it is normalized."""
    client, _ = strain_crud_tester
    created = client.post(ENDPOINT, json={'name': 'Sunset Sherbet', 'effects': None, 'tags': None})
    assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
    assert created.json()['effects'] == []
    assert created.json()['tags'] == []


class TestFiltersNarrowTheList:
    def test_strain_type(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'strain_type': 'indica'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        results = response.json()
        assert [s['name'] for s in results] == ['Granddaddy Purple']

    def test_status(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'status': 'want_to_try'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Runtz']

    def test_effect_matches_inside_the_array(self, strain_crud_tester):
        """An array column is filtered by containment, not by equality."""
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'effect': 'relaxed'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Blue Dream', 'Granddaddy Purple']

        sleepy = client.get(ENDPOINT, params={'effect': 'sleepy'})
        assert [s['name'] for s in sleepy.json()] == ['Granddaddy Purple']

    def test_flavor_matches_inside_the_array(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'flavor': 'grape'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Granddaddy Purple']

    def test_rating_min_is_a_floor(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'rating_min': 8})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Blue Dream']

    def test_an_unmatched_filter_is_an_empty_list(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'strain_type': 'ruderalis'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []

    def test_two_filters_compose(self, strain_crud_tester):
        """Both narrow, rather than the last one winning."""
        client, _ = strain_crud_tester
        both = client.get(ENDPOINT, params={'status': 'tried', 'effect': 'sleepy'})
        assert both.status_code == status.HTTP_200_OK, show_status_and_response(both)
        assert [s['name'] for s in both.json()] == ['Granddaddy Purple']

        contradictory = client.get(ENDPOINT, params={'status': 'want_to_try', 'effect': 'sleepy'})
        assert contradictory.json() == []


class TestUpdate:
    def test_a_patch_leaves_untouched_fields_alone(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        original = client.get(f'{ENDPOINT}{strain_id}/').json()

        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'rating': 10, 'review': 'Revised upward.'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        data = response.json()
        assert data['rating'] == 10
        assert data['review'] == 'Revised upward.'
        assert data['name'] == original['name']
        assert data['effects'] == original['effects']
        assert data['thc_percent'] == original['thc_percent']

    def test_successive_patches_accumulate(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)

        client.patch(f'{ENDPOINT}{strain_id}/', json={'rating': 9})
        client.patch(f'{ENDPOINT}{strain_id}/', json={'source': 'Trailhead Provisions'})
        final = client.patch(f'{ENDPOINT}{strain_id}/', json={'status': 'want_to_try'})

        assert final.status_code == status.HTTP_200_OK, show_status_and_response(final)
        data = final.json()
        assert data['rating'] == 9, 'The first patch survived the third'
        assert data['source'] == 'Trailhead Provisions', 'The second patch survived the third'
        assert data['status'] == 'want_to_try'

    def test_an_array_can_be_replaced(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'effects': ['focused']})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['effects'] == ['focused']

    def test_an_array_can_be_emptied(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'effects': []})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['effects'] == []


class TestVocabularyIsEnforcedOnWrite:
    """The foreign keys cover the two scalars. Nothing but this covers the arrays."""

    def test_an_unknown_effect_is_rejected(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'effects': ['sedative']})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'sedative' in response.json()['detail']

    def test_the_rejection_names_what_would_have_worked(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'effects': ['sedative']})
        assert 'sleepy' in response.json()['detail'], 'A rejection that does not say the valid values is a dead end'

    def test_an_unknown_flavor_is_rejected(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'flavors': ['gasoline']})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_unknown_terpene_is_rejected(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'terpenes': ['pineapplene']})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_unknown_strain_type_is_rejected(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'strain_type': 'indicaa'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_unknown_status_is_rejected(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'status': 'maybe'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_an_update_is_checked_too(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'effects': ['sedative']})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_a_rejected_update_changes_nothing(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        before = client.get(f'{ENDPOINT}{strain_id}/').json()

        client.patch(f'{ENDPOINT}{strain_id}/', json={'notes': 'changed', 'effects': ['sedative']})

        after = client.get(f'{ENDPOINT}{strain_id}/').json()
        assert after['notes'] == before['notes'], 'The valid half of a rejected patch must not land'

    @pytest.mark.parametrize('rating', [0, 11, -1])
    def test_a_rating_outside_one_to_ten_is_rejected(self, strain_crud_tester, rating):
        client, _ = strain_crud_tester
        response = client.post(ENDPOINT, json={'name': 'Typo Kush', 'rating': rating})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestVocabularyEndpoint:
    def test_it_carries_every_defined_value(self, strain_crud_tester):
        """Counted outward from the lookup tables, so an unused value is still listed."""
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}vocabulary/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        vocabulary = response.json()

        effects = {entry['name'] for entry in vocabulary['effects']}
        assert 'giggly' in effects, 'A value no strain uses still has to be offerable'
        assert {'cbd', 'ruderalis'} <= {entry['name'] for entry in vocabulary['types']}
        assert {entry['name'] for entry in vocabulary['statuses']} == {'tried', 'want_to_try'}

    def test_an_unused_value_counts_zero_rather_than_going_missing(self, strain_crud_tester):
        client, _ = strain_crud_tester
        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        counts = {entry['name']: entry['count'] for entry in vocabulary['effects']}
        assert counts['giggly'] == 0
        assert counts['relaxed'] == 2, 'Blue Dream and Granddaddy Purple'
        assert counts['sleepy'] == 1

    def test_scalar_counts_come_from_the_strains(self, strain_crud_tester):
        client, _ = strain_crud_tester
        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        statuses = {entry['name']: entry['count'] for entry in vocabulary['statuses']}
        assert statuses == {'tried': 2, 'want_to_try': 1}

        types = {entry['name']: entry['count'] for entry in vocabulary['types']}
        assert types['indica'] == 1
        assert types['sativa_dominant'] == 1
        assert types['hybrid'] == 0

    def test_every_list_is_sorted_by_name(self, strain_crud_tester):
        client, _ = strain_crud_tester
        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        for key in ('types', 'statuses', 'effects', 'flavors', 'terpenes'):
            names = [entry['name'] for entry in vocabulary[key]]
            assert names == sorted(names), f'{key} came back unsorted'


class TestSearch:
    def test_it_matches_a_name(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}search/', params={'q': 'purple'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Granddaddy Purple']

    def test_it_matches_a_lineage(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}search/', params={'q': 'haze'})
        assert [s['name'] for s in response.json()] == ['Blue Dream']

    def test_it_matches_a_tag(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}search/', params={'q': 'nighttime'})
        assert [s['name'] for s in response.json()] == ['Granddaddy Purple']

    def test_an_empty_query_is_an_empty_list(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}search/', params={'q': '   '})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []


class TestStrainsNotFound:
    def test_read_one_not_found(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_update_not_found(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.patch(f'{ENDPOINT}99999/', json={'name': 'Ghost Kush'})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_delete_not_found(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.delete(f'{ENDPOINT}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)
