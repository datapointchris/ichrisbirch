"""The routes each client scope reaches, as (method, route template) pairs.

A `ScopedClient` reaches a route only when one of its scopes lists it here. Every other route that
resolves a user answers 403. A template is FastAPI's with the router prefix included, so
`/project-items/{id}/` covers every item.
"""

from starlette.routing import BaseRoute

SCOPE_ROUTES: dict[str, frozenset[tuple[str, str]]] = {
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
    """Report whether any of `scopes` lists `route` for `method`."""
    template = getattr(route, 'path', None)
    return any((method, template) in SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)
