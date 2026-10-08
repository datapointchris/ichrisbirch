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

SCOPE = 'icb.project-items.read'
CLIENT = ScopedClient(client_id='icb-svc-worker', scopes=frozenset({SCOPE}))
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': 'testloginadmin@testadmin.com'}
SCOPES_DOCUMENT = Path(__file__).parent / 'testdata' / 'client-scopes.json'

# One request per route `SCOPE` lists, keyed by its template.
SCOPED_URLS = {
    '/project-items/': '/project-items/',
    '/project-items/blocked/': '/project-items/blocked/',
    '/project-items/search/': '/project-items/search/?q=scheduler',
    '/project-items/{id}/': '/project-items/{item}/',
    '/project-items/{id}/blockers/': '/project-items/{item}/blockers/',
    '/project-items/{item_id}/tasks/': '/project-items/{item}/tasks/',
    '/projects/{id}/items/': '/projects/{project}/items/',
}


@pytest.fixture
def as_caller(txn_api):
    """Seed one item in one project. `caller(identity)` sets who the token says is calling and returns the client."""
    client, session = txn_api
    project = models.Project(name='scheduler project')
    item = models.ProjectItem(title='scheduler item')
    session.add_all([project, item])
    session.flush()
    session.add(models.ProjectItemMembership(item_id=item.id, project_id=project.id))
    session.add(models.ProjectItemTask(item_id=item.id, title='scheduler task'))
    session.flush()

    def caller(identity):
        client.app.dependency_overrides[get_oidc_identity] = lambda: identity
        return client

    return SimpleNamespace(caller=caller, item=item, project=project)


@pytest.mark.parametrize(('method', 'template'), sorted(SCOPE_ROUTES[SCOPE]))
def test_a_scoped_client_reads_every_route_its_scope_lists(as_caller, method, template):
    client = as_caller.caller(CLIENT)
    url = SCOPED_URLS[template].format(item=as_caller.item.id, project=as_caller.project.id)
    response = client.request(method, url)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize(
    ('method', 'url'),
    [
        ('POST', '/project-items/'),
        ('GET', '/projects/'),
        ('GET', '/tasks/'),
        ('GET', '/users/me/'),
        ('GET', '/users/1/'),
    ],
    ids=['write-on-a-scoped-router', 'unlisted-read-on-a-scoped-router', 'unscoped-router', 'current-user', 'user-or-none'],
)
def test_a_scoped_client_is_refused_off_its_scopes(as_caller, method, url):
    response = as_caller.caller(CLIENT).request(method, url, json={'title': 'written by a scoped client'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert Refusal.OUTSIDE_CLIENT_SCOPES in response.json()['detail']
    assert 'they reach only GET /project-items/, ' in response.json()['detail']


@pytest.mark.parametrize(('method', 'url'), [('GET', '/tasks/'), ('PATCH', '/project-items/{item}/')])
def test_a_scoped_client_beside_a_forged_remote_user_is_refused(as_caller, method, url):
    """The header strategy resolves that account, so without the refusal the request runs as it."""
    client = as_caller.caller(CLIENT)
    response = client.request(method, url.format(item=as_caller.item.id), headers=FORGED_HEADERS, json={'title': 'renamed'})
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
    """The CLI's suite holds the scope it requests against this file, and its fake provider grants any scope.

    A renamed scope would otherwise pass both suites and answer 403 to every scheduled run. A stale
    file is rewritten here and the test fails, so the change is committed beside the table.
    """
    table = {scope: sorted(f'{method} {template}' for method, template in SCOPE_ROUTES[scope]) for scope in sorted(SCOPE_ROUTES)}
    document = json.dumps(table, indent=2) + '\n'
    if not SCOPES_DOCUMENT.exists() or SCOPES_DOCUMENT.read_text() != document:
        SCOPES_DOCUMENT.parent.mkdir(exist_ok=True)
        SCOPES_DOCUMENT.write_text(document)
        pytest.fail(f'{SCOPES_DOCUMENT} did not hold SCOPE_ROUTES and has been rewritten; commit it')
