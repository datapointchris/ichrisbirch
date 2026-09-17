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

    def test_terpene_matches_inside_the_array(self, strain_crud_tester):
        """Writable through --terpene and the chips, so it is filterable too."""
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'terpene': 'linalool'})
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


class TestARequiredColumnCannotBeBlanked:
    """`name` and `status` are NOT NULL, and a PATCH can name them.

    Without the refusal the blank becomes None in `empty_field_to_none`, survives
    `exclude_unset=True` because the caller named the key, reaches `setattr`, and
    fails at the column as a 500 rather than as a message naming the field.
    """

    @pytest.mark.parametrize('field', ['name', 'status'])
    @pytest.mark.parametrize('value', ['', None, '   '])
    def test_blanking_it_is_a_422_not_a_500(self, strain_crud_tester, field, value):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={field: value})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_the_row_is_untouched_afterwards(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        before = client.get(f'{ENDPOINT}{strain_id}/').json()

        client.patch(f'{ENDPOINT}{strain_id}/', json={'name': None})

        after = client.get(f'{ENDPOINT}{strain_id}/').json()
        assert after['name'] == before['name']
        assert after['status'] == before['status']

    def test_omitting_it_still_leaves_it_alone(self, strain_crud_tester):
        """Omission is how a field is left unchanged, and it stays that way."""
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        before = client.get(f'{ENDPOINT}{strain_id}/').json()

        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'notes': 'only this'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['name'] == before['name']

    @pytest.mark.parametrize('field', ['breeder', 'lineage', 'source', 'notes', 'review'])
    def test_a_nullable_column_still_blanks(self, strain_crud_tester, field):
        """The refusal reaches the two NOT NULL columns and no others."""
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={field: ''})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()[field] is None


class TestAFilterTypoIsRefusedRatherThanAnsweredEmpty:
    """A 200 with no rows reads as an empty catalog, not as a misspelling."""

    @pytest.mark.parametrize(
        ('param', 'value'),
        [
            ('strain_type', 'indicaa'),
            ('status', 'tryed'),
            ('effect', 'sleepyy'),
            ('flavor', 'grapefruit'),
            ('terpene', 'myrcenee'),
        ],
    )
    def test_an_unknown_filter_value_is_a_422(self, strain_crud_tester, param, value):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={param: value})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert value in response.json()['detail']

    def test_the_rejection_names_what_would_have_worked(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'effect': 'sleepyy'})
        assert 'sleepy' in response.json()['detail']

    def test_a_known_value_with_no_rows_is_still_an_empty_list(self, strain_crud_tester):
        """The refusal separates a typo from a real negative; it does not replace it."""
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'effect': 'giggly'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []

    @pytest.mark.parametrize('rating_min', [0, 11, -1])
    def test_a_rating_floor_outside_the_range_is_a_422(self, strain_crud_tester, rating_min):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'rating_min': rating_min})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestTheNaturalKeyRefusesADuplicate:
    """A catalog row needs something an import can upsert on."""

    def test_the_same_name_and_breeder_twice_is_a_409(self, strain_crud_tester):
        client, _ = strain_crud_tester
        first = client.post(ENDPOINT, json={'name': 'Gelato', 'breeder': 'Cookie Fam'})
        assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

        second = client.post(ENDPOINT, json={'name': 'Gelato', 'breeder': 'Cookie Fam'})
        assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)
        assert str(first.json()['id']) in second.json()['detail'], 'The refusal names the row holding the key'

    def test_the_same_name_with_no_breeder_twice_is_a_409(self, strain_crud_tester):
        """NULLS NOT DISTINCT — the unknown breeder is the common case.

        Postgres treats nulls as distinct by default, so without the qualifier
        this is the duplicate that would slip through every time.
        """
        client, _ = strain_crud_tester
        first = client.post(ENDPOINT, json={'name': 'Gelato'})
        assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

        second = client.post(ENDPOINT, json={'name': 'Gelato'})
        assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)

    def test_the_same_name_from_a_different_breeder_is_allowed(self, strain_crud_tester):
        client, _ = strain_crud_tester
        first = client.post(ENDPOINT, json={'name': 'Gelato', 'breeder': 'Cookie Fam'})
        assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

        second = client.post(ENDPOINT, json={'name': 'Gelato', 'breeder': 'Sherbinskis'})
        assert second.status_code == status.HTTP_201_CREATED, show_status_and_response(second)

    def test_a_rename_onto_another_rows_key_is_a_409(self, strain_crud_tester):
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=2)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'name': 'Blue Dream', 'breeder': 'Humboldt Seed Company'})
        assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)

    def test_a_patch_that_keeps_its_own_key_is_not_a_conflict_with_itself(self, strain_crud_tester):
        """The row holding the key is excluded, or every rename would refuse."""
        client, crud_tester = strain_crud_tester
        strain_id = crud_tester.item_id_by_position(client, position=1)
        response = client.patch(f'{ENDPOINT}{strain_id}/', json={'name': 'Blue Dream', 'notes': 'unchanged key'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


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

        rejected = client.patch(f'{ENDPOINT}{strain_id}/', json={'notes': 'changed', 'effects': ['sedative']})
        # Asserted, because a 500 raised inside the check would also leave notes
        # alone and satisfy the assertion below on its own.
        assert rejected.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(rejected)
        assert 'sedative' in rejected.json()['detail']

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
        assert {'cbd', 'ruderalis'} <= {entry['name'] for entry in vocabulary['strain_type']}
        assert {entry['name'] for entry in vocabulary['status']} == {'tried', 'want_to_try'}

    def test_each_list_is_keyed_by_the_field_it_constrains(self, strain_crud_tester):
        """A client matching a 422 detail to its vocabulary should not learn a rename."""
        client, _ = strain_crud_tester
        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        assert set(vocabulary) == {'strain_type', 'status', 'effects', 'flavors', 'terpenes'}

        rejection = client.post(ENDPOINT, json={'name': 'Typo Kush', 'strain_type': 'indicaa'})
        assert rejection.json()['detail'].startswith('strain_type:')

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
        statuses = {entry['name']: entry['count'] for entry in vocabulary['status']}
        assert statuses == {'tried': 2, 'want_to_try': 1}

        types = {entry['name']: entry['count'] for entry in vocabulary['strain_type']}
        assert types['indica'] == 1
        assert types['sativa_dominant'] == 1
        assert types['hybrid'] == 0

    def test_a_value_repeated_inside_one_strain_counts_that_strain_once(self, strain_crud_tester):
        """The count is strains carrying the value, which is what the label claims."""
        client, _ = strain_crud_tester
        created = client.post(ENDPOINT, json={'name': 'Doubled Up', 'effects': ['giggly', 'giggly']})
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['effects'] == ['giggly'], 'A repeat is dropped on write'

        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        counts = {entry['name']: entry['count'] for entry in vocabulary['effects']}
        assert counts['giggly'] == 1

    def test_every_list_is_sorted_by_name(self, strain_crud_tester):
        client, _ = strain_crud_tester
        vocabulary = client.get(f'{ENDPOINT}vocabulary/').json()
        for key in ('strain_type', 'status', 'effects', 'flavors', 'terpenes'):
            names = [entry['name'] for entry in vocabulary[key]]
            assert names == sorted(names), f'{key} came back unsorted'


class TestSearch:
    """`q` narrows the collection read rather than answering from its own route."""

    def test_it_matches_a_name(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'q': 'purple'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [s['name'] for s in response.json()] == ['Granddaddy Purple']

    def test_it_matches_a_lineage(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'q': 'haze'})
        assert [s['name'] for s in response.json()] == ['Blue Dream']

    def test_it_matches_a_tag(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'q': 'nighttime'})
        assert [s['name'] for s in response.json()] == ['Granddaddy Purple']

    def test_a_whitespace_query_matches_nothing_rather_than_everything(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'q': '   '})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json() == []

    def test_it_composes_with_a_filter(self, strain_crud_tester):
        """The whole reason it is a parameter rather than a route."""
        client, _ = strain_crud_tester
        both = client.get(ENDPOINT, params={'q': 'purple', 'status': 'tried'})
        assert [s['name'] for s in both.json()] == ['Granddaddy Purple']
        assert client.get(ENDPOINT, params={'q': 'purple', 'status': 'want_to_try'}).json() == []

    def test_it_composes_with_the_limit(self, strain_crud_tester):
        client, _ = strain_crud_tester
        response = client.get(ENDPOINT, params={'q': 'purple, dream', 'limit': 1})
        assert len(response.json()) == 1


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
