"""`status` on every project-item response, so both doors answer the same document.

The plain-text renderer has always shown a `status` field derived from
`completed` and `archived`. The JSON carried the two booleans and no such key,
so a consumer reading `.status` got null and had to recombine them — which is
what `api-design.md` § "Domain rules live with the domain; the renderer lays out
what it is handed" puts on the server instead.

The field is serialized by every view that renders it, so what a caller sees does
not depend on which command asked.
"""

import pytest
from fastapi import status

from ichrisbirch.models.project import ITEM_STATUSES
from tests.util import show_status_and_response

PROJECTS_ENDPOINT = '/projects/'
PROJECT_ITEMS_ENDPOINT = '/project-items/'


@pytest.fixture
def project_with_items(txn_api_logged_in):
    """One project holding an open, a completed and an archived item."""
    client, _ = txn_api_logged_in
    project = client.post(PROJECTS_ENDPOINT, json={'name': 'Status field'})
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    project_id = project.json()['id']

    created = {}
    for title in ('open item', 'completed item', 'archived item'):
        response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        created[title] = response.json()['id']

    for title, patch in (('completed item', {'completed': True}), ('archived item', {'archived': True})):
        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{created[title]}/', json=patch)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    return client, project_id, created


def by_title(rows) -> dict[str, dict]:
    return {row['title']: row for row in rows}


def test_the_list_carries_a_status_for_every_item(project_with_items):
    client, _, _ = project_with_items
    response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'all'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    rows = by_title(response.json())
    assert rows['open item']['status'] == 'open'
    assert rows['completed item']['status'] == 'completed'
    assert rows['archived item']['status'] == 'archived'


def test_the_detail_read_carries_a_status(project_with_items):
    client, _, created = project_with_items
    response = client.get(f'{PROJECT_ITEMS_ENDPOINT}{created["completed item"]}/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['status'] == 'completed'


def test_the_project_scoped_list_carries_a_status(project_with_items):
    client, project_id, _ = project_with_items
    response = client.get(f'{PROJECTS_ENDPOINT}{project_id}/items/', params={'status': 'all'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    rows = by_title(response.json())
    assert rows['open item']['status'] == 'open'
    assert rows['archived item']['status'] == 'archived'


def test_the_create_response_carries_a_status(txn_api_logged_in):
    """A write answers with the same document a read would."""
    client, _ = txn_api_logged_in
    project = client.post(PROJECTS_ENDPOINT, json={'name': 'Created status'})
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'fresh', 'project_ids': [project.json()['id']]})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['status'] == 'open'


def test_completing_an_item_moves_its_status(project_with_items):
    """The write's own response reports the status it just produced."""
    client, _, created = project_with_items
    response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{created["open item"]}/', json={'completed': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['status'] == 'completed'


def test_the_search_read_carries_a_status(project_with_items):
    client, _, _ = project_with_items
    response = client.get(f'{PROJECT_ITEMS_ENDPOINT}search/', params={'q': 'open item'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert all('status' in row for row in response.json())


def test_the_status_matches_what_the_filter_would_return(project_with_items):
    """The derived field and the `status` filter cannot disagree about an item."""
    client, _, _ = project_with_items
    for item_status in ITEM_STATUSES:
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': item_status})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        reported = {row['status'] for row in response.json()}
        assert reported <= {item_status}, f'a row filtered as {item_status} reported {reported}'


def test_the_booleans_are_still_there(project_with_items):
    """The derived field is additive: a consumer reading the booleans is unaffected."""
    client, _, _ = project_with_items
    response = client.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'all'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    rows = by_title(response.json())
    assert rows['completed item']['completed'] is True
    assert rows['completed item']['archived'] is False
    assert rows['archived item']['archived'] is True
