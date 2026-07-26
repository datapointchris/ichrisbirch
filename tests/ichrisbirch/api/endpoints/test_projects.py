import pytest
from fastapi import status
from sqlalchemy import event
from sqlalchemy.engine import Engine

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


class TestProjectItemRepoLink:
    """The optional `repo` link, by ~/dev/repos.json registry name.

    Nullable on purpose: most items are not repo work (home projects, errands),
    and those stay first-class.
    """

    @pytest.fixture
    def project_id(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client, client.get(PROJECTS_ENDPOINT).json()[0]['id']

    def test_repo_round_trips_through_create_and_read(self, project_id):
        client, pid = project_id
        created = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Fix the brief collision', 'repo': 'forge', 'project_ids': [pid]},
        )
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['repo'] == 'forge', 'create response must echo the repo it stored'

        fetched = client.get(f'{PROJECT_ITEMS_ENDPOINT}{created.json()["id"]}/')
        assert fetched.json()['repo'] == 'forge', 'read must return the stored repo'

    def test_repo_defaults_to_null_for_non_repo_work(self, project_id):
        client, pid = project_id
        response = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Build the microwave cart', 'project_ids': [pid]},
        )
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['repo'] is None

    def test_repo_can_be_set_and_cleared_by_patch(self, project_id):
        client, pid = project_id
        item = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Link me', 'project_ids': [pid]}).json()

        linked = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'repo': 'indy'})
        assert linked.status_code == status.HTTP_200_OK, show_status_and_response(linked)
        assert linked.json()['repo'] == 'indy'

        cleared = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'repo': None})
        assert cleared.json()['repo'] is None, 'null must unlink, matching how notes clears'

    def test_partial_patch_leaves_repo_unchanged(self, project_id):
        client, pid = project_id
        item = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Keep my repo', 'repo': 'forge', 'project_ids': [pid]},
        ).json()

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'title': 'Renamed'})
        assert response.json()['repo'] == 'forge', 'omitting repo must not clear it'


class TestProjectItemMembershipOnLists:
    """The list endpoints carry each item's projects.

    An item title alone ("Glove 80") names a thing without saying what work it is
    part of, so membership travels with every list response rather than costing a
    consumer one detail call per item.
    """

    @pytest.fixture
    def project_id(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client, client.get(PROJECTS_ENDPOINT).json()[0]['id']

    def test_read_many_names_each_items_projects(self, project_id):
        client, pid = project_id
        project_name = client.get(f'{PROJECTS_ENDPOINT}{pid}/').json()['name']
        client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Glove 80', 'project_ids': [pid]})

        response = client.get(PROJECT_ITEMS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        item = next(item for item in response.json() if item['title'] == 'Glove 80')
        assert [project['name'] for project in item['projects']] == [project_name]

    def test_an_item_in_several_projects_names_all_of_them(self, project_id):
        client, pid = project_id
        other = client.post(PROJECTS_ENDPOINT, json={'name': 'A Second Project'}).json()
        item = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Shared work', 'project_ids': [pid]}).json()
        client.post(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/projects/', json={'project_id': other['id']})

        response = client.get(PROJECT_ITEMS_ENDPOINT)

        listed = next(row for row in response.json() if row['title'] == 'Shared work')
        assert 'A Second Project' in [project['name'] for project in listed['projects']]
        assert len(listed['projects']) == 2, 'both memberships must be reported, not an arbitrary first'


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


class TestProjectItemListEmbedsDetail:
    """GET /project-items/ — one request carries everything a sync needs.

    A client reconciling the whole list previously issued two follow-up requests
    per item to collect dependencies and tasks. At 60 items that was 122 serial
    round trips and six seconds, so the list response embeds them instead.
    """

    @pytest.fixture
    def item_with_dependency_and_task(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']

        blocker = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Blocker', 'project_ids': [project_id]})
        blocked = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Blocked', 'project_ids': [project_id]})
        assert blocker.status_code == status.HTTP_201_CREATED, show_status_and_response(blocker)
        assert blocked.status_code == status.HTTP_201_CREATED, show_status_and_response(blocked)
        blocker_id = blocker.json()['id']
        blocked_id = blocked.json()['id']

        dependency = client.post(
            f'{PROJECT_ITEMS_ENDPOINT}{blocked_id}/dependencies/',
            json={'depends_on_id': blocker_id},
        )
        assert dependency.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED), show_status_and_response(dependency)

        task = client.post(f'{PROJECT_ITEMS_ENDPOINT}{blocked_id}/tasks/', json={'title': 'Embedded task'})
        assert task.status_code == status.HTTP_201_CREATED, show_status_and_response(task)

        return client, blocker_id, blocked_id

    def test_list_embeds_dependency_ids(self, item_with_dependency_and_task):
        client, blocker_id, blocked_id = item_with_dependency_and_task

        listed = client.get(PROJECT_ITEMS_ENDPOINT)
        assert listed.status_code == status.HTTP_200_OK, show_status_and_response(listed)
        by_id = {item['id']: item for item in listed.json()}

        assert by_id[blocked_id]['dependency_ids'] == [blocker_id]
        # Present and empty, never absent — a client tells "no dependencies"
        # from "this server predates the field" by whether the key exists.
        assert by_id[blocker_id]['dependency_ids'] == []

    def test_list_embeds_tasks(self, item_with_dependency_and_task):
        client, blocker_id, blocked_id = item_with_dependency_and_task

        by_id = {item['id']: item for item in client.get(PROJECT_ITEMS_ENDPOINT).json()}

        assert [task['title'] for task in by_id[blocked_id]['tasks']] == ['Embedded task']
        assert by_id[blocker_id]['tasks'] == []

    def test_list_matches_the_detail_endpoint(self, item_with_dependency_and_task):
        """The embedded values must agree with the per-item endpoint they replace."""
        client, _, blocked_id = item_with_dependency_and_task

        listed = {item['id']: item for item in client.get(PROJECT_ITEMS_ENDPOINT).json()}[blocked_id]
        detail = client.get(f'{PROJECT_ITEMS_ENDPOINT}{blocked_id}/').json()

        assert listed['dependency_ids'] == detail['dependency_ids']
        assert [p['id'] for p in listed['projects']] == [p['id'] for p in detail['projects']]

    def test_list_query_count_does_not_grow_with_item_count(self, item_with_dependency_and_task):
        """Guards the reason this exists: embedding must not move the N+1 into SQL.

        Asserts flatness rather than a threshold. The absolute count depends on
        auth and fixture queries, but a missing selectinload is what makes the
        count scale with the number of items — measuring the same request at two
        different item counts isolates exactly that.
        """
        client, _, _ = item_with_dependency_and_task

        def selects_issued_listing_items() -> int:
            statements: list[str] = []

            def record(conn, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            # Listening on the Engine class rather than an instance catches
            # whichever engine the transactional fixture bound the session to.
            event.listen(Engine, 'before_cursor_execute', record)
            try:
                response = client.get(PROJECT_ITEMS_ENDPOINT)
                assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
            finally:
                event.remove(Engine, 'before_cursor_execute', record)
            return len([s for s in statements if s.lstrip().upper().startswith('SELECT')])

        baseline = selects_issued_listing_items()

        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']
        for n in range(8):
            created = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': f'Extra {n}', 'project_ids': [project_id]})
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
            client.post(f'{PROJECT_ITEMS_ENDPOINT}{created.json()["id"]}/tasks/', json={'title': f'task {n}'})

        grown = selects_issued_listing_items()
        assert grown == baseline, f'{baseline} SELECTs became {grown} after adding 8 items — eager loading is not applied'
