"""The routes each client scope reaches, as (method, route template) pairs.

A `ScopedClient` reaches a route only when one of its scopes lists it here. Every other route that
resolves a user answers 403. A template is FastAPI's with the router prefix included, so
`/project-items/{id}/` covers every item.
"""

from starlette.routing import BaseRoute

SCOPE_ROUTES: dict[str, frozenset[tuple[str, str]]] = {
    # The reads `icb issues list`, `search`, `next` and `show` make. `--blocked` filters `/issues/`.
    'icb.issues.read': frozenset(
        {
            ('GET', '/issues/'),
            ('GET', '/issues/ready/'),
            ('GET', '/issues/{id}/'),
        }
    ),
    # The reads the `icb projects items` commands make.
    'icb.project-items.read': frozenset(
        {
            ('GET', '/project-items/'),
            ('GET', '/project-items/blocked/'),
            ('GET', '/project-items/search/'),
            ('GET', '/project-items/{id}/'),
            ('GET', '/project-items/{id}/blockers/'),
            ('GET', '/project-items/{item_id}/tasks/'),
            ('GET', '/projects/{id}/items/'),
        }
    ),
}


def permits(scopes: frozenset[str], method: str, route: BaseRoute | None) -> bool:
    template = getattr(route, 'path', None)
    return any((method, template) in SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)


def reachable(scopes: frozenset[str]) -> str:
    """What `scopes` reach, so a refused client reads what it may call from the table that refused it."""
    routes = sorted({f'{method} {template}' for scope in scopes for method, template in SCOPE_ROUTES.get(scope, frozenset())})
    return f'they reach only {", ".join(routes)}' if routes else 'they reach no route'
