"""The routes each client scope reaches, as (method, route template) pairs.

A `ScopedClient` reaches a route only when one of its scopes lists it here. Every other route that
resolves a user answers 403. A template is FastAPI's with every router prefix included, so
`/api/v1/project-items/{id}` covers every item.
"""

from itertools import chain

from starlette.routing import BaseRoute

from ichrisbirch.api import API_PREFIX

SCOPE_ROUTES: dict[str, frozenset[tuple[str, str]]] = {
    # The reads `icb issues list`, `search`, `next`, `show`, and `initiatives list` and `show`
    # make. `--blocked` filters `/issues`. An issue in a series often has no description of its
    # own, so a reader judging it needs its initiative's.
    'icb.issues.read': frozenset(
        {
            ('GET', f'{API_PREFIX}/issues'),
            ('GET', f'{API_PREFIX}/issues/initiatives'),
            ('GET', f'{API_PREFIX}/issues/initiatives/{{id:path}}'),
            ('GET', f'{API_PREFIX}/issues/ready'),
            ('GET', f'{API_PREFIX}/issues/{{id}}'),
        }
    ),
    # The reads the `icb projects items` commands make.
    'icb.project-items.read': frozenset(
        {
            ('GET', f'{API_PREFIX}/project-items'),
            ('GET', f'{API_PREFIX}/project-items/blocked'),
            ('GET', f'{API_PREFIX}/project-items/search'),
            ('GET', f'{API_PREFIX}/project-items/{{id}}'),
            ('GET', f'{API_PREFIX}/project-items/{{id}}/blockers'),
            ('GET', f'{API_PREFIX}/project-items/{{item_id}}/tasks'),
            ('GET', f'{API_PREFIX}/projects/{{id:path}}/items'),
        }
    ),
}


def permits(scopes: frozenset[str], method: str, route: BaseRoute | None) -> bool:
    template = getattr(route, 'path', None)
    return any((method, template) in SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)


def reachable(scopes: frozenset[str]) -> str:
    """What `scopes` reach, so a refused client reads what it may call from the table that refused it."""
    reached = chain.from_iterable(SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)
    routes = sorted({f'{method} {template}' for method, template in reached})
    return f'they reach only {", ".join(routes)}' if routes else 'they reach no route'
