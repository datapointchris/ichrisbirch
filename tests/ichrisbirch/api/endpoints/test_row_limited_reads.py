"""`limit` on the collection reads, and the one meaning zero has across all of them.

One contract across every list endpoint, which is why this is one file rather
than an addition to each: the semantics have to be identical or the shared
`--limit` flag lies about what it does. A positive limit caps, an absent limit
returns everything, and `limit=0` returns nothing — `cli-design.md` § "A
sentinel never steals a value the caller can mean" is the rule, and a reserved
value has to be one no caller could have meant.

Zero is the case worth pinning, and a falsy test is what gets it wrong. `if not
limit` treats it as absence and answers the caller that asked for nothing with
the whole collection, which is a real number really used and nothing on screen
separating it from the other reading.
"""

import pytest
from fastapi import status

from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

# Every list read, with the dataset that seeds it. A resource whose rows arrive
# through a parent relationship is seeded by naming the parent.
LIMITED_READS = [
    ('/articles/', 'articles'),
    ('/autotasks/', 'autotasks'),
    ('/books/', 'books'),
    ('/countdowns/', 'countdowns'),
    ('/events/', 'events'),
    ('/habits/', 'habitcategories'),
    ('/habits/categories/', 'habitcategories'),
    ('/patterns/', 'patterns'),
    ('/projects/', 'projects'),
    ('/recipes/', 'recipes'),
    ('/recipes/cooking-techniques/', 'cooking_techniques'),
    ('/tasks/', 'tasks'),
    ('/tasks/todo/', 'tasks'),
]

READ_IDS = [endpoint for endpoint, _ in LIMITED_READS]


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
        client = seed(dataset)
        uncapped = rows(client.get(endpoint))
        assert len(uncapped) >= 2

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
