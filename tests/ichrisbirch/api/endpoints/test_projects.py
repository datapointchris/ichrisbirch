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


class TestProjectKind:
    """`kind` — what sort of work a project is, from the project_kinds lookup table.

    Exists so a consumer asking "what should I build next" is not handed the next
    errand. Defaults to `build` rather than being required, so every caller that
    predates the column keeps working.
    """

    @pytest.fixture
    def client_with_projects(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client

    def test_kind_defaults_to_build_when_omitted(self, client_with_projects):
        response = client_with_projects.post(PROJECTS_ENDPOINT, json={'name': 'Unclassified project'})
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert response.json()['kind'] == 'build'

    def test_kind_round_trips_through_create_and_read(self, client_with_projects):
        created = client_with_projects.post(PROJECTS_ENDPOINT, json={'name': 'Sell the old keyboard', 'kind': 'chore'})
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()['kind'] == 'chore', 'create response must echo the kind it stored'

        fetched = client_with_projects.get(f'{PROJECTS_ENDPOINT}{created.json()["id"]}/')
        assert fetched.json()['kind'] == 'chore', 'read must return the stored kind'

    def test_read_many_carries_kind(self, client_with_projects):
        projects = client_with_projects.get(PROJECTS_ENDPOINT).json()
        assert {p['kind'] for p in projects} == {'build', 'chore', 'life'}

    def test_kind_can_be_changed_by_patch(self, client_with_projects):
        project = client_with_projects.get(PROJECTS_ENDPOINT).json()[0]

        response = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'kind': 'chore'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['kind'] == 'chore'

    def test_partial_patch_leaves_kind_unchanged(self, client_with_projects):
        project = next(p for p in client_with_projects.get(PROJECTS_ENDPOINT).json() if p['kind'] == 'life')

        response = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'name': 'Renamed'})
        assert response.json()['kind'] == 'life', 'omitting kind must not reset it to the default'

    def test_unknown_kind_is_rejected_on_create(self, client_with_projects):
        """422 rather than the foreign key's 500, and the message names the valid kinds."""
        response = client_with_projects.post(PROJECTS_ENDPOINT, json={'name': 'Bad kind', 'kind': 'errand'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'build' in response.json()['detail']

    def test_unknown_kind_is_rejected_on_patch(self, client_with_projects):
        project = client_with_projects.get(PROJECTS_ENDPOINT).json()[0]

        response = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{project["id"]}/', json={'kind': 'errand'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestProjectStatus:
    """`status` — active / done / dropped, from the project_statuses lookup table.

    A project is a finite effort with a definition of done, so completion IS the
    hide signal and there is no separate archive flag the way items have one. Two
    terminal states rather than one, because `done` alone forces you to lie about
    anything you merely stopped caring about.
    """

    @pytest.fixture
    def client_with_projects(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client

    def create(self, client, **body):
        response = client.post(PROJECTS_ENDPOINT, json=body)
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        return response.json()

    def patch(self, client, project_id, **body):
        return client.patch(f'{PROJECTS_ENDPOINT}{project_id}/', json=body)

    def names(self, client, **params):
        response = client.get(PROJECTS_ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return {p['name'] for p in response.json()}

    def test_status_defaults_to_active_when_omitted(self, client_with_projects):
        created = self.create(client_with_projects, name='Unstated project')
        assert created['status'] == 'active'
        assert created['closed_at'] is None, 'an active project has not been closed'

    def test_completing_hides_the_project_from_the_default_list(self, client_with_projects):
        project = self.create(client_with_projects, name='Finite effort')

        response = self.patch(client_with_projects, project['id'], status='completed')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

        assert 'Finite effort' not in self.names(client_with_projects)
        assert 'Finite effort' in self.names(client_with_projects, status='completed')
        assert 'Finite effort' in self.names(client_with_projects, status='all')

    def test_completing_stamps_closed_at(self, client_with_projects):
        """`created_at` orders by when work started, which is the wrong axis for a finished list."""
        project = self.create(client_with_projects, name='Finite effort')

        completed = self.patch(client_with_projects, project['id'], status='completed').json()

        assert completed['closed_at'] is not None

    def test_dropping_without_a_reason_is_refused(self, client_with_projects):
        """'Deferred' invites re-proposal; the reason is what closes the question."""
        project = self.create(client_with_projects, name='Abandoned effort')

        response = self.patch(client_with_projects, project['id'], status='dropped')

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'reason' in response.json()['detail'].lower()

    def test_dropping_with_a_reason_stores_it(self, client_with_projects):
        project = self.create(client_with_projects, name='Abandoned effort')

        dropped = self.patch(client_with_projects, project['id'], status='dropped', status_reason='Superseded by the other one').json()

        assert dropped['status'] == 'dropped'
        assert dropped['status_reason'] == 'Superseded by the other one'
        assert dropped['closed_at'] is not None

    def test_clearing_the_reason_on_a_dropped_project_is_refused(self, client_with_projects):
        """The CHECK constraint says the same thing; this is the 422 instead of its 500."""
        project = self.create(client_with_projects, name='Abandoned effort')
        self.patch(client_with_projects, project['id'], status='dropped', status_reason='Not worth it')

        response = self.patch(client_with_projects, project['id'], status_reason=None)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_reopening_clears_the_closure(self, client_with_projects):
        project = self.create(client_with_projects, name='Revived effort')
        self.patch(client_with_projects, project['id'], status='dropped', status_reason='Not worth it')

        reopened = self.patch(client_with_projects, project['id'], status='active').json()

        assert reopened['status'] == 'active'
        assert reopened['status_reason'] is None, 'a live project carries no reason for having been closed'
        assert reopened['closed_at'] is None

    def test_unknown_status_is_rejected_on_create(self, client_with_projects):
        response = client_with_projects.post(PROJECTS_ENDPOINT, json={'name': 'Bad status', 'status': 'finished'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'dropped' in response.json()['detail']

    def test_unknown_status_is_rejected_on_patch(self, client_with_projects):
        project = client_with_projects.get(PROJECTS_ENDPOINT).json()[0]

        response = self.patch(client_with_projects, project['id'], status='finished')

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_unknown_status_is_rejected_as_a_filter(self, client_with_projects):
        response = client_with_projects.get(PROJECTS_ENDPOINT, params={'status': 'finished'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)

    def test_status_round_trips_through_create(self, client_with_projects):
        """todoui creates offline and pushes later; a project it finished must not come back active."""
        created = self.create(client_with_projects, name='Finished elsewhere', status='completed')

        assert created['status'] == 'completed'
        assert created['closed_at'] is not None

    def test_closing_a_project_does_not_touch_its_items(self, client_with_projects):
        """'Shipped 8 of 11, dropped with 3 open' is a real signal; eleven archived items is not."""
        project = self.create(client_with_projects, name='Half finished')
        for title, done in (('shipped', True), ('never started', False)):
            item = client_with_projects.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project['id']]}).json()
            if done:
                client_with_projects.patch(f'{PROJECT_ITEMS_ENDPOINT}{item["id"]}/', json={'completed': True})

        self.patch(client_with_projects, project['id'], status='dropped', status_reason='Ran out of road')

        closed = client_with_projects.get(f'{PROJECTS_ENDPOINT}{project["id"]}/').json()
        assert (closed['open_count'], closed['completed_count']) == (1, 1), (
            'the open item was open when the project closed, and that is the useful fact'
        )


class TestProjectNameOwnership:
    """A name is held by the ACTIVE project that bears it, and by nothing else.

    Without the partial unique index a completed `clisteno` owns the name
    forever and the next `clisteno` effort fails on the constraint before any
    resolution rule is consulted.
    """

    @pytest.fixture
    def client_with_projects(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client

    def create(self, client, **body):
        return client.post(PROJECTS_ENDPOINT, json=body)

    def close(self, client, project_id, **body):
        response = client.patch(f'{PROJECTS_ENDPOINT}{project_id}/', json={'status': 'completed', **body})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return response.json()

    def test_two_active_projects_cannot_share_a_name(self, client_with_projects):
        first = self.create(client_with_projects, name='clisteno')
        assert first.status_code == status.HTTP_201_CREATED, show_status_and_response(first)

        second = self.create(client_with_projects, name='clisteno')

        assert second.status_code == status.HTTP_409_CONFLICT, show_status_and_response(second)
        assert first.json()['id'] in second.json()['detail'], 'the conflict must name what already holds it'

    def test_a_finished_project_gives_its_name_back(self, client_with_projects):
        first = self.create(client_with_projects, name='clisteno').json()
        self.close(client_with_projects, first['id'])

        second = self.create(client_with_projects, name='clisteno')

        assert second.status_code == status.HTTP_201_CREATED, show_status_and_response(second)
        assert second.json()['id'] != first['id']

    def test_the_active_project_wins_the_name(self, client_with_projects):
        finished = self.create(client_with_projects, name='clisteno').json()
        self.close(client_with_projects, finished['id'])
        live = self.create(client_with_projects, name='clisteno').json()

        resolved = client_with_projects.get(f'{PROJECTS_ENDPOINT}clisteno/')

        assert resolved.status_code == status.HTTP_200_OK, show_status_and_response(resolved)
        assert resolved.json()['id'] == live['id']

    def test_a_lone_closed_project_is_still_addressable_by_name(self, client_with_projects):
        """Otherwise `icb projects reopen ifiles` cannot name the thing it exists to reopen."""
        finished = self.create(client_with_projects, name='ifiles').json()
        self.close(client_with_projects, finished['id'])

        reopened = client_with_projects.patch(f'{PROJECTS_ENDPOINT}ifiles/', json={'status': 'active'})

        assert reopened.status_code == status.HTTP_200_OK, show_status_and_response(reopened)
        assert reopened.json()['id'] == finished['id']

    def test_several_closed_projects_sharing_a_name_are_ambiguous(self, client_with_projects):
        ids = []
        for _ in range(2):
            project = self.create(client_with_projects, name='clisteno').json()
            self.close(client_with_projects, project['id'])
            ids.append(project['id'])

        resolved = client_with_projects.get(f'{PROJECTS_ENDPOINT}clisteno/')

        assert resolved.status_code == status.HTTP_409_CONFLICT, show_status_and_response(resolved)
        detail = resolved.json()['detail']
        assert all(project_id in detail for project_id in ids), 'the caller needs the ids to disambiguate'

    def test_reopening_into_a_taken_name_is_refused(self, client_with_projects):
        finished = self.create(client_with_projects, name='clisteno').json()
        self.close(client_with_projects, finished['id'])
        self.create(client_with_projects, name='clisteno')

        reopened = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{finished["id"]}/', json={'status': 'active'})

        assert reopened.status_code == status.HTTP_409_CONFLICT, show_status_and_response(reopened)

    def test_renaming_onto_an_active_name_is_refused(self, client_with_projects):
        self.create(client_with_projects, name='clisteno')
        other = self.create(client_with_projects, name='theme').json()

        renamed = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{other["id"]}/', json={'name': 'clisteno'})

        assert renamed.status_code == status.HTTP_409_CONFLICT, show_status_and_response(renamed)

    def test_renaming_onto_a_closed_name_is_allowed(self, client_with_projects):
        finished = self.create(client_with_projects, name='clisteno').json()
        self.close(client_with_projects, finished['id'])
        other = self.create(client_with_projects, name='theme').json()

        renamed = client_with_projects.patch(f'{PROJECTS_ENDPOINT}{other["id"]}/', json={'name': 'clisteno'})

        assert renamed.status_code == status.HTTP_200_OK, show_status_and_response(renamed)


class TestProjectItemCounts:
    """`open_count` / `completed_count` — whether a project still has work in it.

    A total alone cannot answer that: a project with twenty finished items and a
    project with twenty untouched ones both read as "20" in `icb projects list`.
    """

    @pytest.fixture
    def project_with_mixed_items(self, txn_api_logged_in):
        """One project holding an open, a completed, and an archived item."""
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']

        created = {}
        for title in ('open one', 'completed one', 'archived one'):
            response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
            created[title] = response.json()['id']

        for title, patch in (('completed one', {'completed': True}), ('archived one', {'archived': True})):
            response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{created[title]}/', json=patch)
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

        return client, project_id

    def project_from_list(self, client, project_id):
        return next(p for p in client.get(PROJECTS_ENDPOINT).json() if p['id'] == project_id)

    def test_list_splits_items_into_open_and_completed(self, project_with_mixed_items):
        client, project_id = project_with_mixed_items

        project = self.project_from_list(client, project_id)

        assert project['open_count'] == 1
        assert project['completed_count'] == 1

    def test_archived_items_count_toward_neither(self, project_with_mixed_items):
        """Archived beats completed, matching how the clients label a single item."""
        client, project_id = project_with_mixed_items

        project = self.project_from_list(client, project_id)

        assert project['item_count'] == 3, 'the total still counts every membership'
        assert project['item_count'] - project['open_count'] - project['completed_count'] == 1, (
            'the archived item must be the remainder, in neither bucket'
        )

    def test_read_one_agrees_with_the_list(self, project_with_mixed_items):
        client, project_id = project_with_mixed_items

        listed = self.project_from_list(client, project_id)
        detail = client.get(f'{PROJECTS_ENDPOINT}{project_id}/').json()

        counts = ('item_count', 'open_count', 'completed_count')
        assert {k: detail[k] for k in counts} == {k: listed[k] for k in counts}

    def test_project_with_no_items_counts_zero(self, project_with_mixed_items):
        """The outer join must yield 0, not drop the project or return null."""
        client, project_id = project_with_mixed_items
        created = client.post(PROJECTS_ENDPOINT, json={'name': 'Empty project'})

        project = self.project_from_list(client, created.json()['id'])

        assert (project['item_count'], project['open_count'], project['completed_count']) == (0, 0, 0)


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


class TestRepoAsAReadAxis:
    """`repo` filters every collection read, and projects report the repos they touch.

    The repo tag outlives the project an item was filed under, so it is the axis
    that answers "what work has this repo accumulated" across finished and live
    efforts alike. Before this it was write-only, and the question needed jq.
    """

    @pytest.fixture
    def seeded(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        projects = client.get(PROJECTS_ENDPOINT).json()
        first, second = projects[0]['id'], projects[1]['id']
        for title, repo, project in [
            ('Filter items by repo', 'forge', first),
            ('Validate the repo tag', 'forge', first),
            ('Index the notes', 'indy', second),
            ('Build the microwave cart', None, second),
        ]:
            body: dict = {'title': title, 'project_ids': [project]}
            if repo is not None:
                body['repo'] = repo
            created = client.post(PROJECT_ITEMS_ENDPOINT, json=body)
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        return client, first, second

    def test_item_list_filters_to_one_repo(self, seeded):
        client, _, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'repo': 'forge'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert {item['repo'] for item in response.json()} == {'forge'}
        assert len(response.json()) == 2

    def test_empty_repo_asks_for_the_untagged_items(self, seeded):
        client, _, _ = seeded
        response = client.get(PROJECT_ITEMS_ENDPOINT, params={'repo': ''})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert all(item['repo'] is None for item in response.json())
        titles = {item['title'] for item in response.json()}
        assert 'Build the microwave cart' in titles, 'non-repo work has to stay reachable'

    def test_omitting_repo_returns_everything(self, seeded):
        client, _, _ = seeded
        unfiltered = client.get(PROJECT_ITEMS_ENDPOINT).json()
        assert len(unfiltered) >= 4, 'no repo param must not narrow the list'
        assert any(item['repo'] is None for item in unfiltered)
        assert any(item['repo'] == 'forge' for item in unfiltered)

    def test_search_narrows_by_repo(self, seeded):
        client, _, _ = seeded
        both = client.get(f'{PROJECT_ITEMS_ENDPOINT}search/', params={'q': 'the'})
        narrowed = client.get(f'{PROJECT_ITEMS_ENDPOINT}search/', params={'q': 'the', 'repo': 'indy'})
        assert narrowed.status_code == status.HTTP_200_OK, show_status_and_response(narrowed)
        assert {item['repo'] for item in narrowed.json()} == {'indy'}
        assert len(narrowed.json()) < len(both.json())

    def test_project_reports_the_repos_its_items_touch(self, seeded):
        client, first, _ = seeded
        project = client.get(f'{PROJECTS_ENDPOINT}{first}/').json()
        assert project['repos'] == ['forge'], 'deduplicated, and never the null of untagged work'

    def test_a_project_with_no_repo_work_reports_no_repos(self, seeded):
        client, _, second = seeded
        project = client.get(f'{PROJECTS_ENDPOINT}{second}/').json()
        assert project['repos'] == ['indy'], 'the untagged sibling item must not add a null entry'

    def test_project_list_filters_to_projects_touching_a_repo(self, seeded):
        client, first, _ = seeded
        response = client.get(PROJECTS_ENDPOINT, params={'repo': 'forge'})
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert [project['id'] for project in response.json()] == [first]

    def test_filtering_projects_by_repo_does_not_shrink_their_counts(self, seeded):
        client, first, _ = seeded
        unfiltered = client.get(f'{PROJECTS_ENDPOINT}{first}/').json()
        filtered = next(p for p in client.get(PROJECTS_ENDPOINT, params={'repo': 'forge'}).json() if p['id'] == first)
        assert filtered['item_count'] == unfiltered['item_count'], 'HAVING must not double as a row filter'
        assert filtered['open_count'] == unfiltered['open_count']


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


class TestProjectItemStatusFilter:
    """GET /project-items/?status= — three derived states over two booleans.

    An item stores `completed` and `archived` independently. The status filter
    collapses them with archived beating completed, which is the precedence the
    item counts and every client already render — so no combination is reachable
    under two different names.

    The default narrows to open because completed items accumulate without bound.
    Measured 2026-08-12, before this existed: 213 completed against 213 open.
    """

    @pytest.fixture
    def one_of_each_state(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']

        created = {}
        for title in ('still open', 'finished', 'abandoned', 'finished then filed'):
            response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
            assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
            created[title] = response.json()['id']

        for title, patch in (
            ('finished', {'completed': True}),
            ('abandoned', {'archived': True}),
            ('finished then filed', {'completed': True, 'archived': True}),
        ):
            response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{created[title]}/', json=patch)
            assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

        return client

    def titles(self, client, params=None):
        response = client.get(PROJECT_ITEMS_ENDPOINT, params=params)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return {item['title'] for item in response.json()}

    def test_the_default_is_open_only(self, one_of_each_state):
        assert self.titles(one_of_each_state) == {'still open'}

    def test_completed_excludes_the_archived_one(self, one_of_each_state):
        """Archived beats completed, so an item that is both answers to archived alone."""
        assert self.titles(one_of_each_state, {'status': 'completed'}) == {'finished'}

    def test_archived_carries_both_archived_items(self, one_of_each_state):
        assert self.titles(one_of_each_state, {'status': 'archived'}) == {'abandoned', 'finished then filed'}

    def test_all_includes_archived(self, one_of_each_state):
        assert self.titles(one_of_each_state, {'status': 'all'}) == {
            'still open',
            'finished',
            'abandoned',
            'finished then filed',
        }

    def test_the_three_statuses_partition_all(self, one_of_each_state):
        """No item is reachable under two statuses, and none is unreachable."""
        client = one_of_each_state
        buckets = [self.titles(client, {'status': s}) for s in ('open', 'completed', 'archived')]

        assert set.union(*buckets) == self.titles(client, {'status': 'all'})
        assert sum(len(b) for b in buckets) == len(set.union(*buckets)), 'the buckets overlap'

    def test_an_unknown_status_names_the_known_ones(self, one_of_each_state):
        """An empty list would read as a real answer to a question nobody asked."""
        response = one_of_each_state.get(PROJECT_ITEMS_ENDPOINT, params={'status': 'done'})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)
        assert 'completed' in response.json()['detail'], 'the error must name the word that was meant'

    def test_status_composes_with_repo(self, one_of_each_state):
        """Two narrowing filters both apply, rather than the last one winning."""
        client = one_of_each_state
        assert self.titles(client, {'status': 'all', 'repo': 'dotfiles'}) == set()


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


class TestProjectItemReorder:
    """PATCH /project-items/{id}/reorder/ — moving an item shifts its siblings.

    `position` carries no unique constraint, so a bare assignment left two items
    claiming the same slot and the list order fell back to whatever the database
    returned. Every move dense-ranks the project to 0..N-1.
    """

    @pytest.fixture
    def project_with_ordered_items(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        project_id = client.get(PROJECTS_ENDPOINT).json()[0]['id']
        for title in ('First', 'Second', 'Third', 'Fourth'):
            created = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        return client, project_id

    def titles_in_order(self, client, project_id):
        response = client.get(f'{PROJECTS_ENDPOINT}{project_id}/items/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        return [row['title'] for row in response.json()]

    def positions_in_order(self, client, project_id):
        response = client.get(f'{PROJECTS_ENDPOINT}{project_id}/items/')
        return [row['position'] for row in response.json()]

    def item_id_by_title(self, client, project_id, title):
        rows = client.get(f'{PROJECTS_ENDPOINT}{project_id}/items/').json()
        return next(row['id'] for row in rows if row['title'] == title)

    def test_moving_to_the_front_shifts_everything_else_back(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        before = self.titles_in_order(client, project_id)
        target = self.item_id_by_title(client, project_id, before[-1])

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 0})

        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert self.titles_in_order(client, project_id) == [before[-1], *before[:-1]]

    def test_positions_stay_dense_and_unique_after_a_move(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        target = self.item_id_by_title(client, project_id, self.titles_in_order(client, project_id)[2])

        client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 0})

        positions = self.positions_in_order(client, project_id)
        assert positions == list(range(len(positions))), f'expected a dense 0..N-1 sequence, got {positions}'

    def test_repeated_moves_to_the_front_do_not_collide(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        # The reported bug: three moves to position 0 left three items at 0.
        for title in ('Second', 'Third', 'Fourth'):
            target = self.item_id_by_title(client, project_id, title)
            client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 0})

        positions = self.positions_in_order(client, project_id)
        assert len(set(positions)) == len(positions), f'positions collided: {positions}'
        assert self.titles_in_order(client, project_id) == ['Fourth', 'Third', 'Second', 'First']

    def test_moving_within_the_middle_reorders_without_gaps(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        target = self.item_id_by_title(client, project_id, 'First')

        client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 2})

        assert self.titles_in_order(client, project_id) == ['Second', 'Third', 'First', 'Fourth']
        assert self.positions_in_order(client, project_id) == [0, 1, 2, 3]

    def test_position_past_the_end_clamps_to_last(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        target = self.item_id_by_title(client, project_id, 'First')

        response = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 99})

        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert self.titles_in_order(client, project_id) == ['Second', 'Third', 'Fourth', 'First']
        assert self.positions_in_order(client, project_id) == [0, 1, 2, 3]

    def test_reordering_one_project_leaves_another_untouched(self, project_with_ordered_items):
        client, project_id = project_with_ordered_items
        other = client.post(PROJECTS_ENDPOINT, json={'name': 'Untouched Project'}).json()
        for title in ('Alpha', 'Beta'):
            client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [other['id']]})

        target = self.item_id_by_title(client, project_id, 'Fourth')
        client.patch(f'{PROJECT_ITEMS_ENDPOINT}{target}/reorder/', json={'project_id': project_id, 'position': 0})

        assert self.titles_in_order(client, other['id']) == ['Alpha', 'Beta']
        assert self.positions_in_order(client, other['id']) == [0, 1]


class TestProjectItemNumber:
    """The short handle: `number` is what gets printed and typed, `id` is the key.

    Items are created offline in todoui and pushed, so the primary key has to be
    collision-free without a round trip — which is what the UUID buys and why it
    stays. It is a bad handle for the same reason it is a good key: 36 characters
    nobody can retype. The number is server-assigned and every endpoint that
    takes a UUID takes it too.
    """

    @pytest.fixture
    def project_and_client(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client, client.get(PROJECTS_ENDPOINT).json()[0]

    def create_item(self, client, project_id, title='Numbered work'):
        response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': title, 'project_ids': [project_id]})
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        return response.json()

    def test_create_response_carries_the_assigned_number(self, project_and_client):
        client, project = project_and_client
        created = self.create_item(client, project['id'])
        assert isinstance(created['number'], int), 'the create response is where the caller learns its handle'
        assert created['number'] > 0

    def test_each_item_gets_its_own_number(self, project_and_client):
        client, project = project_and_client
        numbers = [self.create_item(client, project['id'], title)['number'] for title in ('One', 'Two', 'Three')]
        assert len(set(numbers)) == 3, f'numbers collided: {numbers}'

    def test_every_read_shape_carries_the_number(self, project_and_client):
        client, project = project_and_client
        created = self.create_item(client, project['id'], 'Visible everywhere')

        detail = client.get(f'{PROJECT_ITEMS_ENDPOINT}{created["id"]}/').json()
        listed = next(row for row in client.get(PROJECT_ITEMS_ENDPOINT).json() if row['id'] == created['id'])
        in_project = next(row for row in client.get(f'{PROJECTS_ENDPOINT}{project["id"]}/items/').json() if row['id'] == created['id'])

        assert detail['number'] == created['number']
        assert listed['number'] == created['number']
        assert in_project['number'] == created['number']

    def test_read_patch_and_delete_accept_the_number(self, project_and_client):
        client, project = project_and_client
        created = self.create_item(client, project['id'], 'Reachable by number')
        number = created['number']

        fetched = client.get(f'{PROJECT_ITEMS_ENDPOINT}{number}/')
        assert fetched.status_code == status.HTTP_200_OK, show_status_and_response(fetched)
        assert fetched.json()['id'] == created['id']

        patched = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{number}/', json={'title': 'Renamed by number'})
        assert patched.status_code == status.HTTP_200_OK, show_status_and_response(patched)
        assert patched.json()['title'] == 'Renamed by number'

        deleted = client.delete(f'{PROJECT_ITEMS_ENDPOINT}{number}/')
        assert deleted.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted)
        assert client.get(f'{PROJECT_ITEMS_ENDPOINT}{created["id"]}/').status_code == status.HTTP_404_NOT_FOUND

    def test_the_uuid_still_works_everywhere_the_number_does(self, project_and_client):
        """Agents hold UUIDs from --json and pass them straight back."""
        client, project = project_and_client
        created = self.create_item(client, project['id'], 'Reachable by uuid')

        fetched = client.get(f'{PROJECT_ITEMS_ENDPOINT}{created["id"]}/')
        assert fetched.status_code == status.HTTP_200_OK, show_status_and_response(fetched)
        assert fetched.json()['number'] == created['number']

    def test_sub_resources_accept_the_number(self, project_and_client):
        client, project = project_and_client
        created = self.create_item(client, project['id'], 'Has sub-resources')
        number = created['number']

        task = client.post(f'{PROJECT_ITEMS_ENDPOINT}{number}/tasks/', json={'title': 'A sub-task'})
        assert task.status_code == status.HTTP_201_CREATED, show_status_and_response(task)
        listed = client.get(f'{PROJECT_ITEMS_ENDPOINT}{number}/tasks/')
        assert [row['title'] for row in listed.json()] == ['A sub-task']

        reordered = client.patch(f'{PROJECT_ITEMS_ENDPOINT}{number}/reorder/', json={'project_id': project['id'], 'position': 0})
        assert reordered.status_code == status.HTTP_200_OK, show_status_and_response(reordered)

        projects = client.get(f'{PROJECT_ITEMS_ENDPOINT}{number}/projects/')
        assert projects.status_code == status.HTTP_200_OK, show_status_and_response(projects)

    def test_a_dependency_can_be_named_by_number_on_both_sides(self, project_and_client):
        client, project = project_and_client
        blocked = self.create_item(client, project['id'], 'Blocked')
        blocker = self.create_item(client, project['id'], 'Blocker')

        linked = client.post(
            f'{PROJECT_ITEMS_ENDPOINT}{blocked["number"]}/dependencies/',
            json={'depends_on_id': blocker['number']},
        )
        assert linked.status_code == status.HTTP_201_CREATED, show_status_and_response(linked)
        assert linked.json()['dependency_ids'] == [blocker['id']]

        unlinked = client.delete(f'{PROJECT_ITEMS_ENDPOINT}{blocked["number"]}/dependencies/{blocker["number"]}/')
        assert unlinked.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(unlinked)

    def test_a_body_reference_may_arrive_as_a_string(self, project_and_client):
        """A CLI forwards what the user typed, so a number reaches the body quoted."""
        client, project = project_and_client
        blocked = self.create_item(client, project['id'], 'Blocked by a string')
        blocker = self.create_item(client, project['id'], 'Blocker named by string')

        linked = client.post(
            f'{PROJECT_ITEMS_ENDPOINT}{blocked["number"]}/dependencies/',
            json={'depends_on_id': str(blocker['number'])},
        )
        assert linked.status_code == status.HTTP_201_CREATED, show_status_and_response(linked)
        assert linked.json()['dependency_ids'] == [blocker['id']]

    def test_an_unknown_number_is_a_404_and_a_non_reference_is_a_422(self, project_and_client):
        client, _ = project_and_client
        assert client.get(f'{PROJECT_ITEMS_ENDPOINT}999999999/').status_code == status.HTTP_404_NOT_FOUND
        assert client.get(f'{PROJECT_ITEMS_ENDPOINT}not-an-item/').status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestProjectNameAsReference:
    """A project answers to its name as well as its UUID.

    Projects get no number because `name` is already unique, so the fix for the
    same unreadable-handle problem is to accept what a person would type.
    """

    @pytest.fixture
    def project_and_client(self, txn_api_logged_in):
        client, session = txn_api_logged_in
        insert_test_data_transactional(session, 'projects')
        return client, client.get(PROJECTS_ENDPOINT).json()[0]

    def test_read_one_accepts_the_name(self, project_and_client):
        client, project = project_and_client
        response = client.get(f'{PROJECTS_ENDPOINT}{project["name"]}/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()['id'] == project['id']

    def test_items_and_patch_accept_the_name(self, project_and_client):
        client, project = project_and_client
        items = client.get(f'{PROJECTS_ENDPOINT}{project["name"]}/items/')
        assert items.status_code == status.HTTP_200_OK, show_status_and_response(items)

        patched = client.patch(f'{PROJECTS_ENDPOINT}{project["name"]}/', json={'description': 'Named, not keyed'})
        assert patched.status_code == status.HTTP_200_OK, show_status_and_response(patched)
        assert patched.json()['description'] == 'Named, not keyed'

    def test_membership_body_accepts_a_project_name(self, project_and_client):
        client, project = project_and_client
        other = client.post(PROJECTS_ENDPOINT, json={'name': 'Named Target'}).json()
        item = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Moves by name', 'project_ids': [project['id']]}).json()

        added = client.post(f'{PROJECT_ITEMS_ENDPOINT}{item["number"]}/projects/', json={'project_id': 'Named Target'})
        assert added.status_code == status.HTTP_201_CREATED, show_status_and_response(added)
        assert added.json()['id'] == other['id']

    def test_create_accepts_a_project_name(self, project_and_client):
        """`--project todoui` is the commonest write there is; demanding a UUID
        there while every read prints a name made the CLI unusable by hand."""
        client, project = project_and_client

        created = client.post(
            PROJECT_ITEMS_ENDPOINT,
            json={'title': 'Filed by name', 'project_ids': [project['name']]},
        )
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert [p['id'] for p in created.json()['projects']] == [project['id']]

    def test_create_against_an_unknown_project_is_a_404(self, project_and_client):
        client, _ = project_and_client
        response = client.post(PROJECT_ITEMS_ENDPOINT, json={'title': 'Nowhere', 'project_ids': ['no-such-project']})
        assert response.status_code == status.HTTP_404_NOT_FOUND, show_status_and_response(response)

    def test_an_unknown_name_is_a_404(self, project_and_client):
        client, _ = project_and_client
        assert client.get(f'{PROJECTS_ENDPOINT}no-such-project/').status_code == status.HTTP_404_NOT_FOUND
