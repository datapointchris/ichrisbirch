import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

PROJECTS_ENDPOINT = '/projects/'
PROJECT_ITEMS_ENDPOINT = '/project-items/'

NEW_PROJECT = schemas.ProjectCreate(
    name='Delta Project new',
    description='Delta project description',
)


@pytest.fixture
def project_crud_tester(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'projects')
    crud_tester = ApiCrudTester(endpoint=PROJECTS_ENDPOINT, new_obj=NEW_PROJECT)
    return client, crud_tester


def test_read_one(project_crud_tester):
    client, crud_tester = project_crud_tester
    crud_tester.test_read_one(client)


def test_read_many(project_crud_tester):
    client, crud_tester = project_crud_tester
    crud_tester.test_read_many(client)


def test_create(project_crud_tester):
    client, crud_tester = project_crud_tester
    crud_tester.test_create(client)


def test_delete(project_crud_tester):
    client, crud_tester = project_crud_tester
    crud_tester.test_delete(client)


def test_lifecycle(project_crud_tester):
    client, crud_tester = project_crud_tester
    crud_tester.test_lifecycle(client)


class TestProjectUpdate:
    """PATCH /projects/{id}/ — field update and null-clearing behaviour."""

    def test_update_name(self, project_crud_tester):
        client, crud_tester = project_crud_tester
        project_id = crud_tester.item_id_by_position(client, position=1)

        response = client.patch(f'{PROJECTS_ENDPOINT}{project_id}/', json={'name': 'Renamed Project'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['name'] == 'Renamed Project'

    def test_update_partial_leaves_description_unchanged(self, project_crud_tester):
        """Patching only name must not touch description (exclude_unset semantics)."""
        client, crud_tester = project_crud_tester
        # Alpha Project has a description
        all_projects = client.get(PROJECTS_ENDPOINT).json()
        project = next(p for p in all_projects if p['description'] is not None)

        response = client.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'name': 'Renamed Only'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['description'] == project['description'], 'Description must not change when not included in patch'

    def test_update_sets_description(self, project_crud_tester):
        """Patching description to a new value persists it."""
        client, crud_tester = project_crud_tester
        all_projects = client.get(PROJECTS_ENDPOINT).json()
        project = next(p for p in all_projects if p['description'] is None)

        response = client.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'description': 'Newly added description'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['description'] == 'Newly added description'

    def test_update_clears_description_with_null(self, project_crud_tester):
        """Patching description to null must clear it — not a no-op.

        This is the key regression test: sending null must be distinct from
        omitting the field. The frontend sends null (not undefined) when the
        user clears the description textarea, so the API must honour it.
        """
        client, crud_tester = project_crud_tester
        all_projects = client.get(PROJECTS_ENDPOINT).json()
        project = next(p for p in all_projects if p['description'] is not None)
        assert project['description'] is not None, 'Precondition: project must have a description'

        response = client.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'description': None})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['description'] is None, 'description must be null after explicit null patch'


class TestProjectItemUpdate:
    """PATCH /project-items/{id}/ — null-clearing behaviour for optional fields."""

    @pytest.fixture
    def project_with_item(self, txn_api_logged_in):
        """Create a project and an item with notes via the API."""
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')

        all_projects = client.get(PROJECTS_ENDPOINT).json()
        project_id = all_projects[0]['id']

        item_resp = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Item with notes', 'notes': 'Original notes text', 'project_ids': [project_id]},
        )
        assert item_resp.status_code == status.HTTP_201_CREATED, show_status_and_response(item_resp)
        return client, item_resp.json()

    def test_update_partial_leaves_notes_unchanged(self, project_with_item):
        """Patching only title must not touch notes."""
        client, item = project_with_item

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'title': 'Renamed item'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['notes'] == 'Original notes text', 'Notes must not change when not included in patch'

    def test_update_clears_notes_with_null(self, project_with_item):
        """Patching notes to null must clear it.

        Same null-vs-omit distinction as test_update_clears_description_with_null.
        The frontend sends null when the user clears the notes textarea.
        """
        client, item = project_with_item
        assert item['notes'] == 'Original notes text', 'Precondition: item must have notes'

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'notes': None})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['notes'] is None, 'notes must be null after explicit null patch'


class TestProjectItemCompletionGuard:
    """PATCH /project-items/{id}/ — cannot complete an item with incomplete tasks."""

    @pytest.fixture
    def item_with_tasks(self, txn_api_logged_in):
        """Create a project, item, and two tasks (one incomplete) via the API."""
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')

        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']

        item_resp = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Item with tasks', 'project_ids': [project_id]},
        )
        assert item_resp.status_code == status.HTTP_201_CREATED, show_status_and_response(item_resp)
        item_id = item_resp.json()['id']

        tasks_endpoint = f'{PROJECT_ITEMS_ENDPOINT}{item_id}/tasks/'
        t1 = client.post(tasks_endpoint, json={'title': 'Task 1'})
        t2 = client.post(tasks_endpoint, json={'title': 'Task 2'})
        assert t1.status_code == status.HTTP_201_CREATED
        assert t2.status_code == status.HTTP_201_CREATED
        task1_id = t1.json()['id']

        # Complete only one of the two tasks
        client.patch(f'{tasks_endpoint}{task1_id}/', json={'completed': True})

        return client, item_id

    def test_cannot_complete_item_with_incomplete_tasks(self, item_with_tasks):
        """Completing an item with outstanding tasks returns 400."""
        client, item_id = item_with_tasks

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item_id}/', json={'completed': True})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, show_status_and_response(response)
        assert 'incomplete task' in response.json()['detail'].lower()

    def test_can_complete_item_when_all_tasks_done(self, item_with_tasks):
        """Completing an item succeeds once all tasks are finished."""
        client, item_id = item_with_tasks

        tasks_endpoint = f'{PROJECT_ITEMS_ENDPOINT}{item_id}/tasks/'
        all_tasks = client.get(tasks_endpoint).json()
        for task in all_tasks:
            if not task['completed']:
                client.patch(f'{tasks_endpoint}{task["id"]}/', json={'completed': True})

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item_id}/', json={'completed': True})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['completed'] is True
