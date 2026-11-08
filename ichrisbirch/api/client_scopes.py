"""The routes each client scope reaches, as (method, route template) pairs.

A `ScopedClient` reaches a route only when one of its scopes lists it here. Every other route that
resolves a user answers 403. A template is FastAPI's with every router prefix included, so
`/api/v1/tasks/{id}` covers every task.
"""

from itertools import chain

from starlette.routing import BaseRoute

from ichrisbirch.api import API_PREFIX

# The read `icb tasks list` makes, `--status completed`, `--since` and `--until` included.
TASKS_READ = frozenset({('GET', f'{API_PREFIX}/tasks')})
# The read `icb articles list` makes, `--since` and `--until` included.
ARTICLES_READ = frozenset({('GET', f'{API_PREFIX}/articles')})
# The read `icb books list` makes, `--since` and `--until` included.
BOOKS_READ = frozenset({('GET', f'{API_PREFIX}/books')})

SCOPE_ROUTES: dict[str, frozenset[tuple[str, str]]] = {
    # Every read `icb overview` fans out to, for a service computing the same lanes: the tasks,
    # articles and books lists, and the reads only the overview makes.
    'icb.overview.read': TASKS_READ
    | ARTICLES_READ
    | BOOKS_READ
    | frozenset(
        {
            ('GET', f'{API_PREFIX}/articles/current'),
            ('GET', f'{API_PREFIX}/countdowns'),
            ('GET', f'{API_PREFIX}/events'),
            ('GET', f'{API_PREFIX}/habits/day'),
        }
    ),
    # The read `icb habits completed` makes, `--since` and `--until` included.
    'icb.habits.read': frozenset({('GET', f'{API_PREFIX}/habits/completed')}),
    'icb.tasks.read': TASKS_READ,
    'icb.articles.read': ARTICLES_READ,
    'icb.books.read': BOOKS_READ,
}


def permits(scopes: frozenset[str], method: str, route: BaseRoute | None) -> bool:
    template = getattr(route, 'path', None)
    return any((method, template) in SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)


def reachable(scopes: frozenset[str]) -> str:
    """What `scopes` reach, so a refused client reads what it may call from the table that refused it."""
    reached = chain.from_iterable(SCOPE_ROUTES.get(scope, frozenset()) for scope in scopes)
    routes = sorted({f'{method} {template}' for method, template in reached})
    return f'they reach only {", ".join(routes)}' if routes else 'they reach no route'
