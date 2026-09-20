"""`limit` on the collection reads, and the one meaning zero has across all of them.

One contract across every list endpoint, which is why this is one file rather
than an addition to each: the semantics have to be identical or the shared
`--limit` flag lies about what it does. A positive limit caps, an absent limit
returns everything, and `limit=0` returns nothing. A reserved value has to be
one no caller could have meant, and `tail -n 0` settles that a caller can mean
zero rows.

Zero is the case worth pinning, and a falsy test is what gets it wrong. `if not
limit` treats it as absence and answers the caller that asked for nothing with
the whole collection, which is a real number really used and nothing on screen
separating it from the other reading.
"""

import typing
from typing import get_origin

import pytest
from fastapi import status
from pydantic import BaseModel

from ichrisbirch.services.row_limit import CappedRowLimit
from ichrisbirch.services.row_limit import RowLimit
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

# Every list read, with the dataset that seeds it. A resource whose rows arrive
# through a parent relationship is seeded by naming the parent.
LIMITED_READS = [
    ('/articles/', 'articles'),
    ('/autotasks/', 'autotasks'),
    ('/books/', 'books'),
    ('/box-packing/boxes/', 'boxes'),
    ('/box-packing/items/', 'boxes'),
    ('/countdowns/', 'countdowns'),
    ('/events/', 'events'),
    ('/habits/', 'habitcategories'),
    ('/habits/categories/', 'habitcategories'),
    ('/habits/completed/', 'habitcategories'),
    ('/patterns/', 'patterns'),
    ('/projects/', 'projects'),
    ('/recipes/', 'recipes'),
    ('/recipes/cooking-techniques/', 'cooking_techniques'),
    ('/strains/', 'strains'),
    ('/tasks/', 'tasks'),
    ('/tasks/todo/', 'tasks'),
]

READ_IDS = [endpoint for endpoint, _ in LIMITED_READS]

# Collection reads that take no limit today. This is the backlog, not a blessing:
# most of these answer with rows that grow outside the binary and should take
# `RowLimit`. Four are decided rather than pending, and each answers something a
# cap would make wrong rather than shorter:
#
#   /admin/config/         a config block, not a paged collection
#   /admin/system/health/  one status report
#   /strains/vocabulary/   the whole declared vocabulary, which a client reads to
#                          build its dropdowns — a short one offers fewer values
#   /habits/day/           one day's board, bounded by the habits you track. A cap
#                          hides a habit you still owe, and `current_total` would
#                          then disagree with the list beside it
#
# It is a ratchet. The walk below fails on a new uncapped read, so the set can
# only shrink, and removing an entry is what capping that read looks like.
UNCAPPED_READS = {
    '/admin/config/',
    '/admin/scheduler/jobs/',
    '/admin/system/errors/',
    '/admin/system/health/',
    '/api-keys/',
    '/articles/failed-imports/',
    '/articles/search/',
    '/autofun/',
    '/books/search/',
    '/box-packing/items/orphans/',
    '/box-packing/search/',
    '/coffee/beans/',
    '/coffee/shops/',
    '/durations/',
    '/habits/day/',
    '/money-wasted/',
    '/project-items/blocked/',
    '/project-items/search/',
    '/project-items/{id}/blockers/',
    '/project-items/{id}/projects/',
    '/project-items/{item_id}/tasks/',
    '/recipes/cooking-techniques/categories/',
    '/recipes/cooking-techniques/search/',
    '/recipes/search-by-ingredients/',
    '/recipes/search/',
    '/recipes/stats/',
    '/strains/vocabulary/',
    '/tasks/completed/',
    '/tasks/search/',
}

# The two declarations a read may take. Both carry the floor; they differ only in
# whether absence is a spelling the read offers.
SHARED_LIMITS = (RowLimit, CappedRowLimit)


@pytest.fixture
def seed(txn_api_logged_in):
    """Insert one dataset and hand back the client that can read it."""
    client, session = txn_api_logged_in

    def _seed(dataset: str):
        insert_test_data_transactional(session, dataset)
        return client

    return _seed


def rows(response) -> list:
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    return response.json()


@pytest.mark.parametrize(('endpoint', 'dataset'), LIMITED_READS, ids=READ_IDS)
class TestEveryListReadTakesALimit:
    def test_the_seed_gives_this_read_something_to_cap(self, seed, endpoint, dataset):
        """Guards the two cases below: a dataset that stops seeding makes them vacuous."""
        client = seed(dataset)
        assert len(rows(client.get(endpoint))) >= 2

    def test_a_positive_limit_caps_the_rows(self, seed, endpoint, dataset):
        client = seed(dataset)
        assert len(rows(client.get(endpoint, params={'limit': 1}))) == 1

    def test_zero_asks_for_no_rows(self, seed, endpoint, dataset):
        """A falsy test would answer this with the whole collection instead."""
        client = seed(dataset)
        assert rows(client.get(endpoint, params={'limit': 0})) == []

    def test_an_absent_limit_is_the_only_thing_that_returns_every_row(self, seed, endpoint, dataset):
        """Compared against a limit above the population, not against a floor.

        A `>= 2` assertion here is the seed guard written twice: it holds against an
        implementation capping the absent read at two, which is the one thing the name
        claims cannot happen."""
        client = seed(dataset)
        assert len(rows(client.get(endpoint))) == len(rows(client.get(endpoint, params={'limit': 1000})))

    def test_a_negative_limit_is_a_422(self, seed, endpoint, dataset):
        """Rejected at the edge by name rather than reaching SQL as a negative."""
        client = seed(dataset)
        response = client.get(endpoint, params={'limit': -1})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


class TestProjectItemReadsTakeALimit:
    """`/project-items/` and `/projects/{id}/items/` are seeded through the API.

    A scope selects which rows come back, never what a filter means, so both
    paths take the same parameter and read zero the same way.
    """

    @pytest.fixture
    def seeded_project(self, txn_api_logged_in):
        client, _ = txn_api_logged_in
        project = client.post('/projects/', json={'name': 'Row limited reads'})
        assert project.status_code == status.HTTP_201_CREATED, show_status_and_response(project)
        project_id = project.json()['id']
        for title in ('first item', 'second item', 'third item'):
            created = client.post('/project-items/', json={'title': title, 'project_ids': [project_id]})
            assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        return client, project_id

    def test_the_flat_list_caps(self, seeded_project):
        client, _ = seeded_project
        assert len(rows(client.get('/project-items/', params={'limit': 2}))) == 2

    def test_the_flat_list_reads_zero_as_no_rows(self, seeded_project):
        client, _ = seeded_project
        assert rows(client.get('/project-items/', params={'limit': 0})) == []

    def test_the_project_scoped_list_caps(self, seeded_project):
        client, project_id = seeded_project
        assert len(rows(client.get(f'/projects/{project_id}/items/', params={'limit': 2}))) == 2

    def test_the_project_scoped_list_reads_zero_as_no_rows(self, seeded_project):
        client, project_id = seeded_project
        assert rows(client.get(f'/projects/{project_id}/items/', params={'limit': 0})) == []

    def test_the_limit_composes_with_status(self, seeded_project):
        """Two narrowing filters both apply, rather than the last one winning."""
        client, _ = seeded_project
        response = client.get('/project-items/', params={'status': 'all', 'limit': 1})
        assert len(rows(response)) == 1

    def test_a_negative_limit_is_a_422(self, seeded_project):
        client, _ = seeded_project
        response = client.get('/project-items/', params={'limit': -1})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


def collection_reads(api) -> dict:
    """Every GET route answering with rows, read off the app rather than listed.

    `LIMITED_READS` above is a written list, and nothing fails when an endpoint is
    missing from it — which is how two box-packing reads kept a falsy limit long
    after the helper existed. This walks the routes instead, so an endpoint that
    answers with a collection is covered by being registered.
    """
    from fastapi.routing import APIRoute

    found: dict[str, APIRoute] = {}
    for route in api.routes:
        if not isinstance(route, APIRoute) or 'GET' not in route.methods:
            continue
        if answers_with_rows(route.response_model):
            found[route.path] = route
    return found


def answers_with_rows(model) -> bool:
    """Whether a response model carries rows a caller would want to cap.

    A bare `list[...]` is the common shape. An envelope holding lists beside its
    scalars carries rows just the same, and a walk keyed on the outer type alone
    stops seeing them the first time someone wraps a collection.

    A model declaring `id` is one resource, and a list inside it is a part of
    that row: a recipe's ingredients, a project's items. Capping those cuts a
    relationship rather than a page. An envelope has no identity of its own, so
    its lists are the whole answer.

    A field spelled `list[X] | None` is a list too, so the union's arguments are
    checked rather than only its origin.
    """
    if carries_rows(model):
        return True
    if not (isinstance(model, type) and issubclass(model, BaseModel)):
        return False
    if 'id' in model.model_fields:
        return False
    return any(carries_rows(field.annotation) for field in model.model_fields.values())


def carries_rows(annotation) -> bool:
    """Whether an annotation is a list, or a union with a list in it."""
    if get_origin(annotation) is list:
        return True
    return any(get_origin(arg) is list for arg in typing.get_args(annotation))


def limit_annotation(route) -> object | None:
    """The declared type of the route's `limit` parameter, or None when it has none."""
    return typing.get_type_hints(route.endpoint, include_extras=True).get('limit')


def test_every_read_that_takes_a_limit_declares_the_shared_one(txn_api_logged_in):
    """One helper is what keeps every endpoint on the same side of zero.

    A read declaring its own `int | None` gets no floor, so a negative reaches SQL,
    and a hand-written falsy test answers a zero with the whole collection. Both are
    invisible in the response, which is why this asserts the declaration rather than
    a status code.

    Scoped to reads that take a limit at all. Which reads must take one is the
    test below.
    """
    reads = collection_reads(txn_api_logged_in[0].app)
    taking_a_limit = {path: route for path, route in reads.items() if limit_annotation(route) is not None}

    assert len(taking_a_limit) >= len(LIMITED_READS), 'the walk found fewer limited reads than the list above it'
    wrong = {path: limit_annotation(route) for path, route in taking_a_limit.items() if limit_annotation(route) not in SHARED_LIMITS}
    assert wrong == {}, f'reads declaring their own limit rather than a shared one: {wrong}'


def test_every_collection_read_takes_a_limit(txn_api_logged_in):
    """A new collection read takes a limit, and an uncapped one is named in the set.

    The caller that cannot cap has to fetch the whole collection to discard most of
    it, and nothing on screen says so. `/habits/completed/` sat like that while its
    two sibling reads had a limit, which is the drift this catches.

    Both directions are asserted, so capping a read fails here until its entry comes
    out of UNCAPPED_READS. That is what stops the backlog being edited by accident.
    """
    reads = collection_reads(txn_api_logged_in[0].app)
    missing = {path for path, route in reads.items() if limit_annotation(route) is None}

    assert missing - UNCAPPED_READS == set(), 'collection reads taking no limit'
    assert UNCAPPED_READS - missing == set(), 'exempted reads that now take a limit'


def test_the_written_list_names_no_endpoint_the_app_does_not_serve(txn_api_logged_in):
    """`LIMITED_READS` drives the cases above, so a stale path silently stops testing one."""
    served = set(collection_reads(txn_api_logged_in[0].app))

    assert {endpoint for endpoint, _ in LIMITED_READS} <= served
