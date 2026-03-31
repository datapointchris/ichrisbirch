"""Tests for client-provided UUID7 IDs on create endpoints.

Verifies that Projects, ProjectItems, and ProjectItemTasks accept an optional
client-provided `id` field and return 409 on duplicate IDs.
"""

from uuid import uuid7

from fastapi import status

from tests.util import show_status_and_response

PROJECTS_ENDPOINT = '/projects/'
PROJECT_ITEMS_ENDPOINT = '/project-items/'


def _create_project(client, **overrides):
    """Helper to create a project, returning the response."""
    payload = {'name': f'Test Project {uuid7()}', 'description': 'test'} | overrides
    return client.post(PROJECTS_ENDPOINT, json=payload)


def _create_project_item(client, project_id, **overrides):
    """Helper to create a project item, returning the response."""
    payload = {'title': f'Test Item {uuid7()}', 'project_ids': [str(project_id)]} | overrides
    return client.post(PROJECT_ITEMS_ENDPOINT, json=payload)


def _create_task(client, item_id, **overrides):
    """Helper to create a project item task, returning the response."""
    payload = {'title': f'Test Task {uuid7()}'} | overrides
    return client.post(f'{PROJECT_ITEMS_ENDPOINT}{item_id}/tasks/', json=payload)


# --- Projects ---


def test_create_project_with_client_id(txn_api_logged_in):
    client, _session = txn_api_logged_in
    client_id = str(uuid7())
    response = _create_project(client, id=client_id)
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['id'] == client_id


def test_create_project_duplicate_id_409(txn_api_logged_in):
    client, _session = txn_api_logged_in
    client_id = str(uuid7())
    first = _create_project(client, id=client_id, name='First')
    assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

    second = _create_project(client, id=client_id, name='Second')
    assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)


# --- Project Items ---


def test_create_project_item_with_client_id(txn_api_logged_in):
    client, _session = txn_api_logged_in
    project = _create_project(client)
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    project_id = project.json()['id']

    client_id = str(uuid7())
    response = _create_project_item(client, project_id, id=client_id)
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['id'] == client_id


def test_create_project_item_duplicate_id_409(txn_api_logged_in):
    client, _session = txn_api_logged_in
    project = _create_project(client)
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    project_id = project.json()['id']

    client_id = str(uuid7())
    first = _create_project_item(client, project_id, id=client_id, title='First')
    assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

    second = _create_project_item(client, project_id, id=client_id, title='Second')
    assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)


# --- Project Item Tasks ---


def test_create_task_with_client_id(txn_api_logged_in):
    client, _session = txn_api_logged_in
    project = _create_project(client)
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    project_id = project.json()['id']

    item = _create_project_item(client, project_id)
    assert item.status_code == status.HTTP_201_CREATED, show_status_and_response(item)
    item_id = item.json()['id']

    client_id = str(uuid7())
    response = _create_task(client, item_id, id=client_id)
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    assert response.json()['id'] == client_id


def test_create_task_duplicate_id_409(txn_api_logged_in):
    client, _session = txn_api_logged_in
    project = _create_project(client)
    assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
    project_id = project.json()['id']

    item = _create_project_item(client, project_id)
    assert item.status_code == status.HTTP_201_CREATED, show_status_and_response(item)
    item_id = item.json()['id']

    client_id = str(uuid7())
    first = _create_task(client, item_id, id=client_id, title='First')
    assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

    second = _create_task(client, item_id, id=client_id, title='Second')
    assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)
