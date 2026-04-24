import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

ENDPOINT = '/recipes/cooking-techniques/'
NEW_OBJ = schemas.CookingTechniqueCreate(
    name='Maillard Sear',
    category='heat_application',
    summary='High, dry heat on protein surface for deep browning.',
    body='Pat protein dry. Hot pan + high-smoke-point oil. Do not move the protein for 2-3 minutes.',
    why_it_works='Amino acids + reducing sugars at >285F produce Maillard browning compounds.',
    common_pitfalls='Wet surface produces steam instead of a sear.',
    tags=['sear', 'protein', 'maillard'],
    rating=5,
)


@pytest.fixture
def cooking_technique_crud_tester(txn_api_logged_in):
    """Provide ApiCrudTester with transactional test data."""
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'cooking_techniques')
    crud_tester = ApiCrudTester(endpoint=ENDPOINT, new_obj=NEW_OBJ, verify_attr='name')
    return client, crud_tester


def test_read_one(cooking_technique_crud_tester):
    client, crud_tester = cooking_technique_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(cooking_technique_crud_tester):
    client, crud_tester = cooking_technique_crud_tester
    crud_tester.test_read_many(client)


def test_create(cooking_technique_crud_tester):
    client, crud_tester = cooking_technique_crud_tester
    crud_tester.test_create(client)


def test_delete(cooking_technique_crud_tester):
    client, crud_tester = cooking_technique_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(cooking_technique_crud_tester):
    client, crud_tester = cooking_technique_crud_tester
    crud_tester.test_lifecycle(client)


def test_create_auto_slugifies(cooking_technique_crud_tester):
    """POST without slug should generate one from name."""
    client, _ = cooking_technique_crud_tester
    response = client.post(ENDPOINT, json=NEW_OBJ.model_dump(mode='json'))
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['slug'] == 'maillard-sear'


def test_create_slug_collision_suffix(cooking_technique_crud_tester):
    """Creating two techniques with the same name should produce distinct slugs."""
    client, _ = cooking_technique_crud_tester
    payload = NEW_OBJ.model_dump(mode='json')
    first = client.post(ENDPOINT, json=payload)
    assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)
    second = client.post(ENDPOINT, json=payload)
    assert second.status_code == status.HTTP_201_CREATED, show_status_and_response(second)
    assert first.json()['slug'] == 'maillard-sear'
    assert second.json()['slug'] == 'maillard-sear-2'


def test_list_filter_by_category(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(ENDPOINT, params={'category': 'flavor_development'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    names = {t['name'] for t in response.json()}
    assert names == {'Test Caramelize Paste'}


def test_list_filter_by_rating_min(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(ENDPOINT, params={'rating_min': 5})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    names = {t['name'] for t in response.json()}
    assert names == {'Test Vinaigrette Ratio'}


def test_search_by_name(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'vinaigrette'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Vinaigrette Ratio'


def test_search_by_body(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'brick'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Caramelize Paste'


def test_search_by_tag(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}search/', params={'q': 'beans'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Test Bean Soak'


def test_categories_endpoint_includes_all_nine(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}categories/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    data = response.json()
    assert len(data) == 9
    # Counts reflect test data: 1 in each of the 3 seeded categories
    counts_by_name = {row['name']: row['count'] for row in data}
    assert counts_by_name['composition_and_ratio'] == 1
    assert counts_by_name['flavor_development'] == 1
    assert counts_by_name['preservation_and_pre_treatment'] == 1
    # Unseeded categories are present with count 0
    assert counts_by_name['heat_application'] == 0
    assert counts_by_name['dough_and_batter'] == 0


def test_read_by_slug(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}slug/test-vinaigrette-ratio/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['name'] == 'Test Vinaigrette Ratio'


def test_read_by_slug_not_found(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    response = client.get(f'{ENDPOINT}slug/does-not-exist/')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_does_not_change_slug(cooking_technique_crud_tester):
    """Renaming a technique must preserve the existing slug."""
    client, crud_tester = cooking_technique_crud_tester
    first_id = crud_tester.item_id_by_position(client, position=1)
    before = client.get(f'{ENDPOINT}{first_id}/').json()
    original_slug = before['slug']

    response = client.patch(f'{ENDPOINT}{first_id}/', json={'name': 'Renamed Technique'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['name'] == 'Renamed Technique'
    assert response.json()['slug'] == original_slug


def test_create_rejects_invalid_rating(cooking_technique_crud_tester):
    client, _ = cooking_technique_crud_tester
    payload = NEW_OBJ.model_dump(mode='json')
    payload['rating'] = 7
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
