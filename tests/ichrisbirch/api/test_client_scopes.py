"""The routes a scoped client's token reaches, through the real app and the real dependency chain.

`get_oidc_identity` is overridden to return the caller, so these cover the gate. The token itself is
covered in `test_oidc_auth.py`.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import status

from ichrisbirch import models
from ichrisbirch.api.client_scopes import SCOPE_ROUTES
from ichrisbirch.api.exceptions import Refusal
from ichrisbirch.api.oidc_auth import OIDCIdentity
from ichrisbirch.api.oidc_auth import ScopedClient
from ichrisbirch.api.oidc_auth import get_oidc_identity
from tests.util import show_status_and_response

PROJECT_ITEMS = 'icb.project-items.read'
ISSUES = 'icb.issues.read'
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': 'testloginadmin@testadmin.com'}
SCOPES_DOCUMENT = Path(__file__).parent / 'testdata' / 'client-scopes.json'

# One request per route any scope lists, keyed by its template. The issue reads are the ones the
# CLI sends: search widens the status to all, and show names the issue by number.
SCOPED_URLS = {
    '/issues/': '/issues/?search=scheduler&status=all',
    '/issues/ready/': '/issues/ready/',
    '/issues/{id}/': '/issues/{issue}/',
    '/project-items/': '/project-items/',
    '/project-items/blocked/': '/project-items/blocked/',
    '/project-items/search/': '/project-items/search/?q=scheduler',
    '/project-items/{id}/': '/project-items/{item}/',
    '/project-items/{id}/blockers/': '/project-items/{item}/blockers/',
    '/project-items/{item_id}/tasks/': '/project-items/{item}/tasks/',
    '/projects/{id}/items/': '/projects/{project}/items/',
}

SCOPED_ROUTES = sorted((scope, method, template) for scope, routes in SCOPE_ROUTES.items() for method, template in routes)

# How a refusal's list of what each scope reaches begins.
REACHES = {
    ISSUES: 'GET /issues/, GET /issues/ready/, GET /issues/{id}/',
    PROJECT_ITEMS: 'GET /project-items/, ',
}


def scoped(scope: str) -> ScopedClient:
    return ScopedClient(client_id='icb-svc-worker', scopes=frozenset({scope}))


@pytest.fixture
def as_caller(txn_api):
    """Seed one item in one project, and one issue.

    `caller(identity)` sets who the token says is calling and returns the client, and `url(template)`
    fills a template with the seeded rows.
    """
    client, session = txn_api
    project = models.Project(name='scheduler project')
    item = models.ProjectItem(title='scheduler item')
    issue = models.Issue(title='scheduler issue', rank=1.0)
    session.add_all([project, item, issue])
    session.flush()
    session.add(models.ProjectItemMembership(item_id=item.id, project_id=project.id))
    session.add(models.ProjectItemTask(item_id=item.id, title='scheduler task'))
    session.flush()

    def caller(identity):
        client.app.dependency_overrides[get_oidc_identity] = lambda: identity
        return client

    def url(template):
        return template.format(item=item.id, project=project.id, issue=issue.number)

    return SimpleNamespace(caller=caller, url=url, project=project)


@pytest.mark.parametrize(('scope', 'method', 'template'), SCOPED_ROUTES)
def test_a_scoped_client_reads_every_route_its_scope_lists(as_caller, scope, method, template):
    response = as_caller.caller(scoped(scope)).request(method, as_caller.url(SCOPED_URLS[template]))
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [
        (PROJECT_ITEMS, 'POST', '/project-items/'),
        (PROJECT_ITEMS, 'GET', '/projects/'),
        (PROJECT_ITEMS, 'GET', '/issues/'),
        (PROJECT_ITEMS, 'GET', '/tasks/'),
        (PROJECT_ITEMS, 'GET', '/users/me/'),
        (PROJECT_ITEMS, 'GET', '/users/1/'),
        (ISSUES, 'POST', '/issues/'),
        (ISSUES, 'PATCH', '/issues/{issue}/'),
        (ISSUES, 'DELETE', '/issues/{issue}/'),
        (ISSUES, 'POST', '/issues/ready/claim/'),
        (ISSUES, 'POST', '/issues/{issue}/claim/'),
        (ISSUES, 'POST', '/issues/{issue}/comments/'),
        (ISSUES, 'GET', '/issues/{issue}/comments/'),
        (ISSUES, 'GET', '/issues/vocabulary/'),
        (ISSUES, 'GET', '/issues/labels/'),
        (ISSUES, 'GET', '/project-items/'),
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
        'issues-another-scopes-route',
    ],
)
def test_a_scoped_client_is_refused_off_its_scopes(as_caller, scope, method, url):
    response = as_caller.caller(scoped(scope)).request(method, as_caller.url(url), json={'title': 'written by a scoped client'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert Refusal.OUTSIDE_CLIENT_SCOPES in response.json()['detail']
    assert f'they reach only {REACHES[scope]}' in response.json()['detail']


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [(PROJECT_ITEMS, 'GET', '/tasks/'), (PROJECT_ITEMS, 'PATCH', '/project-items/{item}/'), (ISSUES, 'PATCH', '/issues/{issue}/')],
)
def test_a_scoped_client_beside_a_forged_remote_user_is_refused(as_caller, scope, method, url):
    """The header strategy resolves that account, so without the refusal the request runs as it."""
    client = as_caller.caller(scoped(scope))
    response = client.request(method, as_caller.url(url), headers=FORGED_HEADERS, json={'title': 'renamed'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


def test_a_scope_the_table_does_not_name_reaches_nothing(as_caller):
    client = as_caller.caller(ScopedClient(client_id='icb-svc-worker', scopes=frozenset({'icb.unknown'})))
    response = client.get('/project-items/')
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert 'they reach no route' in response.json()['detail']


def test_a_person_on_a_scoped_router_resolves_as_the_user(as_caller):
    client = as_caller.caller(OIDCIdentity(subject='authelia-user-uuid', client_id='icb-cli-macmini'))
    response = client.post('/project-items/', json={'title': 'written by a person', 'project_ids': [str(as_caller.project.id)]})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)


def test_no_credentials_on_a_scoped_router_is_still_401(as_caller):
    response = as_caller.caller(None).get('/project-items/')
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
