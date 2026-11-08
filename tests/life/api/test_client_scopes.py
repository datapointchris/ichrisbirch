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

from life.api import API_PREFIX
from life.api.client_scopes import SCOPE_ROUTES
from life.api.exceptions import Refusal
from life.api.oidc_auth import OIDCIdentity
from life.api.oidc_auth import ScopedClient
from life.api.oidc_auth import get_oidc_identity
from tests.util import show_status_and_response

OVERVIEW = 'life.overview.read'
HABITS = 'life.habits.read'
TASKS = 'life.tasks.read'
ARTICLES = 'life.articles.read'
BOOKS = 'life.books.read'
SINCE = 'since=2026-01-01T00:00:00Z&until=2026-02-01T00:00:00Z'
SERVICE = 'life-svc-worker'
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': 'testloginadmin@testadmin.com'}
SCOPES_DOCUMENT = Path(__file__).parent / 'testdata' / 'client-scopes.json'

# One request per route any scope lists, keyed by its template. The windowed lists carry the
# `--since` and `--until` a day's or a week's history is read with.
SCOPED_URLS = {
    f'{API_PREFIX}/articles': f'/articles?{SINCE}',
    f'{API_PREFIX}/articles/current': '/articles/current',
    f'{API_PREFIX}/books': f'/books?{SINCE}',
    f'{API_PREFIX}/countdowns': '/countdowns',
    f'{API_PREFIX}/events': '/events?when=upcoming',
    f'{API_PREFIX}/habits/completed': f'/habits/completed?{SINCE}',
    f'{API_PREFIX}/habits/day': '/habits/day',
    f'{API_PREFIX}/tasks': f'/tasks?status=completed&{SINCE}',
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
    """`caller(identity)` sets who the token says is calling and returns the client."""
    client, _ = txn_api

    def caller(identity):
        client.app.dependency_overrides[get_oidc_identity] = lambda: identity
        return client

    return SimpleNamespace(caller=caller)


@pytest.mark.parametrize(('scope', 'method', 'template'), SCOPED_ROUTES)
def test_a_scoped_client_reaches_every_route_its_scope_lists(as_caller, scope, method, template):
    response = as_caller.caller(scoped(scope)).request(method, SCOPED_URLS[template])
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [
        (OVERVIEW, 'POST', '/tasks'),
        (OVERVIEW, 'GET', '/habits'),
        (OVERVIEW, 'GET', '/recipes'),
        (OVERVIEW, 'GET', '/users/me'),
        (OVERVIEW, 'GET', '/users/1'),
        (HABITS, 'GET', '/habits/day'),
        (TASKS, 'GET', '/tasks/completed'),
        (ARTICLES, 'GET', '/articles/current'),
        (BOOKS, 'GET', '/articles'),
    ],
    ids=[
        'overview-write-on-a-scoped-router',
        'overview-unlisted-read-on-a-scoped-router',
        'overview-unscoped-router',
        'overview-current-user',
        'overview-user-or-none',
        'habits-a-read-only-overview-lists',
        'tasks-unlisted-read-on-a-scoped-router',
        'articles-a-read-only-overview-lists',
        'books-another-scopes-route',
    ],
)
def test_a_scoped_client_is_refused_off_its_scopes(as_caller, scope, method, url):
    response = as_caller.caller(scoped(scope)).request(method, url, json={'name': 'written by a scoped client'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    message = response.json()['message']
    assert Refusal.OUTSIDE_CLIENT_SCOPES in message
    assert all(f'{method} {template}' in message for method, template in SCOPE_ROUTES[scope])


@pytest.mark.parametrize(
    ('scope', 'method', 'url'),
    [
        (OVERVIEW, 'GET', '/recipes'),
        (OVERVIEW, 'PATCH', '/tasks/1'),
    ],
)
def test_a_scoped_client_beside_a_forged_remote_user_is_refused(as_caller, scope, method, url):
    """The header strategy resolves that account, so without the refusal the request runs as it."""
    client = as_caller.caller(scoped(scope))
    response = client.request(method, url, headers=FORGED_HEADERS, json={'name': 'renamed'})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


def test_a_scope_the_table_does_not_name_reaches_nothing(as_caller):
    client = as_caller.caller(ScopedClient(client_id='life-svc-worker', scopes=frozenset({'life.unknown'})))
    response = client.get('/tasks')
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)


def test_a_person_on_a_scoped_router_resolves_as_the_user(as_caller):
    client = as_caller.caller(OIDCIdentity(subject='authelia-user-uuid', client_id='life-cli-laptop'))
    response = client.post('/tasks', json={'name': 'written by a person', 'category': 'Chore'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)


def test_no_credentials_on_a_scoped_router_is_still_401(as_caller):
    response = as_caller.caller(None).get('/tasks')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


def test_the_document_the_cli_reads_holds_the_scope_table():
    """The CLI's suite holds the scope it requests, and every request it sends, against this file.

    Its fake provider grants the scope the CLI spells, so a scope renamed here would otherwise pass
    both suites and answer 403 to every service run. A stale file is rewritten here and the test
    fails, so the change is committed beside the table.
    """
    table = {scope: sorted(f'{method} {template}' for method, template in SCOPE_ROUTES[scope]) for scope in sorted(SCOPE_ROUTES)}
    document = json.dumps(table, indent=2) + '\n'
    if not SCOPES_DOCUMENT.exists() or SCOPES_DOCUMENT.read_text() != document:
        SCOPES_DOCUMENT.parent.mkdir(exist_ok=True)
        SCOPES_DOCUMENT.write_text(document)
        pytest.fail(f'{SCOPES_DOCUMENT} did not hold SCOPE_ROUTES and has been rewritten; commit it')
