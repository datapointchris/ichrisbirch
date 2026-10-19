"""The routes a scoped client's token reaches, through the real app and the real dependency chain.

`get_oidc_identity` is overridden to return the caller, so these cover the gate. The token itself is
covered in `test_oidc_auth.py`.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import status

from ichrisbirch import models
from ichrisbirch.api import API_PREFIX
from ichrisbirch.api.client_scopes import SCOPE_ROUTES
from ichrisbirch.api.exceptions import Refusal
from ichrisbirch.api.oidc_auth import OIDCIdentity
from ichrisbirch.api.oidc_auth import ScopedClient
from ichrisbirch.api.oidc_auth import get_oidc_identity
from tests.util import show_status_and_response

PROJECT_ITEMS = 'icb.project-items.read'
ISSUES = 'icb.issues.read'
CLAIM = 'icb.issues.claim'
CLOSE = 'icb.issues.close'
PLAN = 'icb.issues.plan'
CLOSER = 'worker/close-job@service-box'
SERVICE = 'icb-svc-worker'
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': 'testloginadmin@testadmin.com'}
SCOPES_DOCUMENT = Path(__file__).parent / 'testdata' / 'client-scopes.json'

# One request per route any scope lists, keyed by its template. The issue reads are the ones the
# CLI sends: search widens the status to all, and show names the issue by number.
SCOPED_URLS = {
    f'{API_PREFIX}/issues': '/issues?search=scheduler&status=all',
    f'{API_PREFIX}/issues/ready': '/issues/ready',
    f'{API_PREFIX}/issues/vocabulary': '/issues/vocabulary',
    f'{API_PREFIX}/issues/{{id}}': '/issues/{issue}',
    f'{API_PREFIX}/issues/initiatives': '/issues/initiatives',
    f'{API_PREFIX}/issues/initiatives/{{id:path}}': '/issues/initiatives/{initiative}',
    f'{API_PREFIX}/project-items': '/project-items',
    f'{API_PREFIX}/project-items/blocked': '/project-items/blocked',
    f'{API_PREFIX}/project-items/search': '/project-items/search?q=scheduler',
    f'{API_PREFIX}/project-items/{{id}}': '/project-items/{item}',
    f'{API_PREFIX}/project-items/{{id}}/blockers': '/project-items/{item}/blockers',
    f'{API_PREFIX}/project-items/{{item_id}}/tasks': '/project-items/{item}/tasks',
    f'{API_PREFIX}/projects/{{id:path}}/items': '/projects/{project}/items',
}

# Each write a scope lists, as the CLI sends it: the claim holding the issue for the fix agent and
# its release, the comment saying what landed, the update that completes the issue and names the job
# closing it, and each edit a planning job makes to the queue.
SCOPED_WRITES = {
    (CLAIM, 'POST', f'{API_PREFIX}/issues/{{id}}/claim'): (
        '/issues/{issue}/claim',
        {'claimant': SERVICE, 'minutes': 60},
        status.HTTP_200_OK,
    ),
    (CLAIM, 'DELETE', f'{API_PREFIX}/issues/{{id}}/claim'): ('/issues/{issue}/claim', None, status.HTTP_200_OK),
    (CLOSE, 'POST', f'{API_PREFIX}/issues/{{id}}/comments'): (
        '/issues/{issue}/comments',
        {'body': 'Landed: a merged fix'},
        status.HTTP_201_CREATED,
    ),
    (CLOSE, 'PATCH', f'{API_PREFIX}/issues/{{id}}'): ('/issues/{issue}', {'status': 'completed', 'closed_by': CLOSER}, status.HTTP_200_OK),
    (PLAN, 'PATCH', f'{API_PREFIX}/issues/{{id}}'): ('/issues/{issue}', {'priority': 2, 'initiative': '{initiative}'}, status.HTTP_200_OK),
    (PLAN, 'POST', f'{API_PREFIX}/issues/{{id}}/rank'): ('/issues/{issue}/rank', {'after': '{neighbor}'}, status.HTTP_200_OK),
    (PLAN, 'POST', f'{API_PREFIX}/issues'): (
        '/issues',
        {'title': 'left of the initiative', 'initiative': '{initiative}', 'status': 'triage'},
        status.HTTP_201_CREATED,
    ),
    (PLAN, 'POST', f'{API_PREFIX}/issues/initiatives'): (
        '/issues/initiatives',
        {'name': 'grouped by a planning job'},
        status.HTTP_201_CREATED,
    ),
    (PLAN, 'PATCH', f'{API_PREFIX}/issues/initiatives/{{id:path}}'): (
        '/issues/initiatives/{initiative}',
        {'status': 'dropped', 'status_reason': 'merged into another'},
        status.HTTP_200_OK,
    ),
}


def scoped_routes() -> Iterator[tuple[str, str, str]]:
    for scope, routes in SCOPE_ROUTES.items():
        for method, template in routes:
            yield scope, method, template


SCOPED_ROUTES = sorted(scoped_routes())


def scoped(scope: str) -> ScopedClient:
    return ScopedClient(client_id=SERVICE, scopes=frozenset({scope}))


@pytest.fixture
def as_caller(txn_api):
    """Seed one item in one project, two issues of one priority, and one initiative.

    `caller(identity)` sets who the token says is calling and returns the client, and `url(template)`
    fills a template with the seeded rows. The initiative is named, as the CLI names one.
    """
    client, session = txn_api
    project = models.Project(name='scheduler project')
    item = models.ProjectItem(title='scheduler item')
    issue = models.Issue(title='scheduler issue', rank=1.0)
    neighbor = models.Issue(title='scheduler neighbor', rank=2.0)
    initiative = models.Initiative(name='scheduler-initiative')
    session.add_all([project, item, issue, neighbor, initiative])
    session.flush()
    session.add(models.ProjectItemMembership(item_id=item.id, project_id=project.id))
    session.add(models.ProjectItemTask(item_id=item.id, title='scheduler task'))
    session.flush()

    def caller(identity):
        client.app.dependency_overrides[get_oidc_identity] = lambda: identity
        return client

    def url(template):
        return template.format(item=item.id, project=project.id, issue=issue.number, neighbor=neighbor.number, initiative=initiative.name)

    return SimpleNamespace(caller=caller, url=url, project=project)


@pytest.mark.parametrize(('scope', 'method', 'template'), SCOPED_ROUTES)
def test_a_scoped_client_reaches_every_route_its_scope_lists(as_caller, scope, method, template):
    if method == 'GET':
        url, body, expected = SCOPED_URLS[template], None, status.HTTP_200_OK
    else:
        url, body, expected = SCOPED_WRITES[(scope, method, template)]
        body = body and {key: as_caller.url(value) if isinstance(value, str) else value for key, value in body.items()}
    response = as_caller.caller(scoped(scope)).request(method, as_caller.url(url), json=body)
    assert response.status_code == expected, show_status_and_response(response)


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [
        (PROJECT_ITEMS, 'POST', '/project-items'),
        (PROJECT_ITEMS, 'GET', '/projects'),
        (PROJECT_ITEMS, 'GET', '/issues'),
        (PROJECT_ITEMS, 'GET', '/tasks'),
        (PROJECT_ITEMS, 'GET', '/users/me'),
        (PROJECT_ITEMS, 'GET', '/users/1'),
        (ISSUES, 'POST', '/issues'),
        (ISSUES, 'PATCH', '/issues/{issue}'),
        (ISSUES, 'DELETE', '/issues/{issue}'),
        (ISSUES, 'POST', '/issues/ready/claim'),
        (ISSUES, 'POST', '/issues/{issue}/claim'),
        (ISSUES, 'POST', '/issues/{issue}/comments'),
        (ISSUES, 'GET', '/issues/{issue}/comments'),
        (ISSUES, 'GET', '/issues/vocabulary'),
        (ISSUES, 'GET', '/issues/labels'),
        (ISSUES, 'POST', '/issues/initiatives'),
        (ISSUES, 'PATCH', '/issues/initiatives/{initiative}'),
        (ISSUES, 'DELETE', '/issues/initiatives/{initiative}'),
        (ISSUES, 'GET', '/project-items'),
        (CLOSE, 'GET', '/issues/{issue}'),
        (CLOSE, 'POST', '/issues'),
        (CLOSE, 'DELETE', '/issues/{issue}'),
        (CLOSE, 'POST', '/issues/{issue}/claim'),
        (CLOSE, 'PATCH', '/issues/initiatives/{initiative}'),
        (CLAIM, 'POST', '/issues/ready/claim'),
        (CLAIM, 'PATCH', '/issues/{issue}'),
        (PLAN, 'DELETE', '/issues/{issue}'),
        (PLAN, 'DELETE', '/issues/initiatives/{initiative}'),
    ],
    ids=[
        'project-items-write-on-a-scoped-router',
        'project-items-unlisted-read-on-a-scoped-router',
        'project-items-another-scopes-route',
        'project-items-unscoped-router',
        'project-items-current-user',
        'project-items-user-or-none',
        'issues-create',
        'issues-update',
        'issues-delete',
        'issues-claim-next',
        'issues-claim-one',
        'issues-comment',
        'issues-unlisted-read-on-a-scoped-router',
        'issues-vocabulary',
        'issues-labels-router',
        'issues-initiatives-create',
        'issues-initiatives-update',
        'issues-initiatives-delete',
        'issues-another-scopes-route',
        'close-read',
        'close-create',
        'close-delete',
        'close-claim',
        'close-initiative-update',
        'claim-the-queues-head',
        'claim-update',
        'plan-delete',
        'plan-initiative-delete',
    ],
)
def test_a_scoped_client_is_refused_off_its_scopes(as_caller, scope, method, url):
    response = as_caller.caller(scoped(scope)).request(method, as_caller.url(url), json={'title': 'written by a scoped client'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    message = response.json()['message']
    assert Refusal.OUTSIDE_CLIENT_SCOPES in message
    assert all(f'{method} {template}' in message for method, template in SCOPE_ROUTES[scope])


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [
        (PROJECT_ITEMS, 'GET', '/tasks'),
        (PROJECT_ITEMS, 'PATCH', '/project-items/{item}'),
        (ISSUES, 'PATCH', '/issues/{issue}'),
        (ISSUES, 'PATCH', '/issues/initiatives/{initiative}'),
        (CLOSE, 'PATCH', '/issues/{issue}'),
    ],
)
def test_a_scoped_client_beside_a_forged_remote_user_is_refused(as_caller, scope, method, url):
    """The header strategy resolves that account, so without the refusal the request runs as it."""
    client = as_caller.caller(scoped(scope))
    response = client.request(method, as_caller.url(url), headers=FORGED_HEADERS, json={'title': 'renamed'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


ONLY_CLOSES = Refusal.SCOPED_CLIENT_ONLY_CLOSES
ONLY_PRIORITY_AND_INITIATIVE = Refusal.SCOPED_CLIENT_ONLY_SETS_PRIORITY_AND_INITIATIVE


@pytest.mark.parametrize(
    ('scopes', 'body', 'refusal', 'refused'),
    [
        ({CLOSE}, {'status': 'completed', 'title': 'renamed'}, ONLY_CLOSES, 'title'),
        ({CLOSE}, {'priority': 0}, ONLY_CLOSES, 'priority'),
        ({CLOSE}, {'status': 'in_progress'}, ONLY_CLOSES, 'status'),
        ({PLAN}, {'status': 'completed'}, ONLY_PRIORITY_AND_INITIATIVE, 'status'),
        ({PLAN, CLOSE}, {'title': 'renamed'}, ONLY_PRIORITY_AND_INITIATIVE, 'title'),
        ({PLAN, CLOSE}, {'status': 'completed', 'priority': 2}, ONLY_CLOSES, 'priority'),
    ],
    ids=[
        'close-an-edit-beside-a-close',
        'close-an-edit-alone',
        'close-a-status-that-keeps-it-open',
        'plan-a-close',
        'both-a-title',
        'both-an-edit-beside-a-close',
    ],
)
def test_a_scoped_update_is_a_close_or_sets_only_priority_and_initiative(as_caller, scopes, body, refusal, refused):
    client = as_caller.caller(ScopedClient(client_id=SERVICE, scopes=frozenset(scopes)))
    response = client.patch(as_caller.url('/issues/{issue}'), json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert refusal in response.json()['message']
    assert refused in response.json()['message']


@pytest.mark.parametrize(
    'body',
    [{'title': 'ready on its own'}, {'title': 'holds its parent back', 'status': 'triage', 'parent': '{issue}'}],
    ids=['an-open-filing', 'a-filing-under-a-parent'],
)
def test_a_scoped_filing_goes_into_triage_under_no_parent(as_caller, body):
    body = {key: as_caller.url(value) for key, value in body.items()}
    response = as_caller.caller(scoped(PLAN)).post(as_caller.url('/issues'), json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert Refusal.SCOPED_CLIENT_FILES_ONLY_INTO_TRIAGE in response.json()['message']


def test_the_close_scope_signs_with_its_client_id_and_closes_an_issue_once(as_caller):
    client = as_caller.caller(scoped(CLOSE))
    url = as_caller.url('/issues/{issue}')
    closed = client.patch(url, json={'status': 'completed'})
    assert closed.status_code == status.HTTP_200_OK, show_status_and_response(closed)
    assert closed.json()['closed_by'] == 'icb-svc-worker'

    moved = client.patch(url, json={'status': 'canceled'})
    assert moved.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(moved)
    assert Refusal.SCOPED_CLIENT_ONLY_CLOSES in moved.json()['message']
    assert 'completed' in moved.json()['message']


def test_the_claim_scope_holds_an_issue_under_its_own_id_and_frees_only_that(as_caller):
    """Release frees whoever holds the issue, so without the narrowing a job could free a session's work."""
    url = as_caller.url('/issues/{issue}/claim')
    person = OIDCIdentity(subject='authelia-user-uuid', client_id='icb-cli-laptop')
    assert as_caller.caller(person).post(url, json={'claimant': 'claude-code/peer'}).status_code == status.HTTP_200_OK

    service = as_caller.caller(scoped(CLAIM))
    freed = service.delete(url)
    assert freed.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(freed)
    assert Refusal.SCOPED_CLIENT_RELEASES_ITS_OWN in freed.json()['message']
    assert 'claimed by claude-code/peer' in freed.json()['message']

    as_caller.caller(person).delete(url)
    service = as_caller.caller(scoped(CLAIM))
    signed = service.post(url, json={'claimant': 'claude-code/peer'})
    assert signed.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(signed)
    assert Refusal.SCOPED_CLIENT_CLAIMS_AS_ITSELF in signed.json()['message']

    held = service.post(url, json={'claimant': SERVICE})
    assert held.status_code == status.HTTP_200_OK, show_status_and_response(held)
    assert held.json()['claimed_by'] == SERVICE
    released = service.delete(url)
    assert released.status_code == status.HTTP_200_OK, show_status_and_response(released)
    assert released.json()['status'] == 'open'


def test_a_scope_the_table_does_not_name_reaches_nothing(as_caller):
    client = as_caller.caller(ScopedClient(client_id='icb-svc-worker', scopes=frozenset({'icb.unknown'})))
    response = client.get('/project-items')
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert 'they reach no route' in response.json()['message']


def test_a_person_on_a_scoped_router_resolves_as_the_user(as_caller):
    client = as_caller.caller(OIDCIdentity(subject='authelia-user-uuid', client_id='icb-cli-macmini'))
    response = client.post('/project-items', json={'title': 'written by a person', 'project_ids': [str(as_caller.project.id)]})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)


def test_no_credentials_on_a_scoped_router_is_still_401(as_caller):
    response = as_caller.caller(None).get('/project-items')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


def test_the_document_the_cli_reads_holds_the_scope_table():
    """The CLI's suite holds the scope it requests, and every request it sends, against this file.

    Its fake provider grants the scope the CLI spells, so a scope renamed here would otherwise pass
    both suites and answer 403 to every scheduled run. A stale file is rewritten here and the test
    fails, so the change is committed beside the table.
    """
    table = {scope: sorted(f'{method} {template}' for method, template in SCOPE_ROUTES[scope]) for scope in sorted(SCOPE_ROUTES)}
    document = json.dumps(table, indent=2) + '\n'
    if not SCOPES_DOCUMENT.exists() or SCOPES_DOCUMENT.read_text() != document:
        SCOPES_DOCUMENT.parent.mkdir(exist_ok=True)
        SCOPES_DOCUMENT.write_text(document)
        pytest.fail(f'{SCOPES_DOCUMENT} did not hold SCOPE_ROUTES and has been rewritten; commit it')
