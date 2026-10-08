"""The routes a service token reaches, through the real app and the real dependency chain.

`get_oidc_identity` is overridden to return the caller, so these cover the gate. The token itself is
covered in `test_oidc_auth.py`.
"""

from types import SimpleNamespace

import pytest
from fastapi import status
from fastapi.routing import APIRoute

from ichrisbirch import models
from ichrisbirch.api.exceptions import Refusal
from ichrisbirch.api.main import create_api
from ichrisbirch.api.oidc_auth import OIDCIdentity
from ichrisbirch.api.oidc_auth import ServicePrincipal
from ichrisbirch.api.oidc_auth import get_oidc_identity
from ichrisbirch.api.service_scopes import SCOPE_ROUTES
from tests.util import show_status_and_response
from tests.utils.database import test_settings

SCOPE = 'icb.project-items.read'
SERVICE = ServicePrincipal(client_id='icb-svc-worker', scopes=frozenset({SCOPE}))
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': 'testloginadmin@testadmin.com'}

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


@pytest.fixture(scope='module')
def served_routes() -> set[tuple[str, str]]:
    api = create_api(settings=test_settings)
    return {(method, route.path) for route in api.routes if isinstance(route, APIRoute) for method in route.methods}


@pytest.fixture
def as_caller(txn_api):
    """Seed one item in one project, and return a function that sets who the token says is calling."""
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


@pytest.mark.parametrize(
    ('method', 'template'),
    sorted((method, template) for routes in SCOPE_ROUTES.values() for method, template in routes),
)
def test_every_scoped_route_is_one_the_app_serves(served_routes, method, template):
    """`permits` matches templates exactly, so a renamed path parameter locks the service out."""
    assert (method, template) in served_routes


@pytest.mark.parametrize(('method', 'template'), sorted(SCOPE_ROUTES[SCOPE]))
def test_a_service_reads_every_route_its_scope_lists(as_caller, method, template):
    client = as_caller.caller(SERVICE)
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
def test_a_service_is_refused_off_its_scope(as_caller, method, url):
    response = as_caller.caller(SERVICE).request(method, url, json={'title': 'written by a service'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert Refusal.OUTSIDE_SERVICE_SCOPE in response.json()['detail']


@pytest.mark.parametrize(('method', 'url'), [('GET', '/tasks/'), ('PATCH', '/project-items/{item}/')])
def test_a_service_token_beside_a_forged_remote_user_is_refused(as_caller, method, url):
    """The header strategy resolves that account, so without the refusal the request runs as it."""
    client = as_caller.caller(SERVICE)
    response = client.request(method, url.format(item=as_caller.item.id), headers=FORGED_HEADERS, json={'title': 'renamed'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


def test_a_scope_the_table_does_not_name_reaches_nothing(as_caller):
    client = as_caller.caller(ServicePrincipal(client_id='icb-svc-worker', scopes=frozenset({'icb.unknown'})))
    response = client.get('/project-items/')
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


def test_a_person_on_a_scoped_router_resolves_as_the_user(as_caller):
    client = as_caller.caller(OIDCIdentity(subject='authelia-user-uuid', client_id='icb-cli-macmini'))
    response = client.post('/project-items/', json={'title': 'written by a person', 'project_ids': [str(as_caller.project.id)]})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)


def test_no_credentials_on_a_scoped_router_is_still_401(as_caller):
    response = as_caller.caller(None).get('/project-items/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)
