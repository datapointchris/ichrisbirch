import pytest
from fastapi import status

from ichrisbirch import schemas
from tests.util import show_status_and_response
from tests.utils.database import insert_test_data_transactional

from .crud_test import ApiCrudTester

INITIATIVES = '/issues/initiatives/'

NEW_INITIATIVE = schemas.InitiativeCreate(name='Move dev items into issues', priority=1)


@pytest.fixture
def client(txn_api_logged_in):
    client, session = txn_api_logged_in
    insert_test_data_transactional(session, 'issue_initiatives')
    return client


def ok(response, code=status.HTTP_200_OK):
    assert response.status_code == code, show_status_and_response(response)
    return response.json()


def names(rows) -> list[str]:
    return [row['name'] for row in rows]


def test_lifecycle(client):
    ApiCrudTester(endpoint=INITIATIVES, new_obj=NEW_INITIATIVE, expected_length=2).test_lifecycle(client)


def test_active_initiatives_order_by_priority_with_none_last(client):
    ok(client.post(INITIATIVES, json={'name': 'Urgent cleanup', 'priority': 1}), status.HTTP_201_CREATED)
    assert names(ok(client.get(INITIATIVES))) == ['Urgent cleanup', 'Ship the issue tracker', 'Retire the old capture path']


def test_finished_initiatives_follow_the_active_ones(client):
    assert names(ok(client.get(INITIATIVES, params={'status': 'all'})))[-1] == 'Finished migration'


def test_an_initiative_answers_to_its_name(client):
    assert ok(client.get(f'{INITIATIVES}Ship the issue tracker/'))['priority'] == 2


def test_counts_partition_the_issues_and_repos_name_the_work_done_or_left(client):
    created = {
        repo: ok(
            client.post('/issues/', json={'title': repo, 'repo': repo, 'initiative': 'Ship the issue tracker'}), status.HTTP_201_CREATED
        )
        for repo in ('ichrisbirch', 'dotfiles', 'todoui')
    }
    ok(client.patch(f'/issues/{created["dotfiles"]["number"]}/', json={'status': 'completed'}))
    ok(client.patch(f'/issues/{created["todoui"]["number"]}/', json={'status': 'canceled', 'status_reason': 'Moved'}))

    counted = ok(client.get(f'{INITIATIVES}Ship the issue tracker/'))
    assert (counted['issue_count'], counted['open_count'], counted['completed_count'], counted['canceled_count']) == (3, 1, 1, 1)
    assert counted['repos'] == ['dotfiles', 'ichrisbirch']


def test_dropping_needs_a_reason(client):
    response = client.patch(f'{INITIATIVES}Retire the old capture path/', json={'status': 'dropped'})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, show_status_and_response(response)


def test_closing_stamps_and_reopening_clears(client):
    closed = ok(client.patch(f'{INITIATIVES}Retire the old capture path/', json={'status': 'dropped', 'status_reason': 'Folded in'}))
    assert closed['closed_ts'] is not None
    reopened = ok(client.patch(f'{INITIATIVES}{closed["id"]}/', json={'status': 'active'}))
    assert (reopened['closed_ts'], reopened['status_reason']) == (None, None)


def test_only_one_active_initiative_holds_a_name(client):
    response = client.post(INITIATIVES, json={'name': 'Ship the issue tracker'})
    assert response.status_code == status.HTTP_409_CONFLICT, show_status_and_response(response)
    ok(client.post(INITIATIVES, json={'name': 'Finished migration'}), status.HTTP_201_CREATED)


def test_a_closed_initiative_stops_lending_its_priority(client):
    created = ok(client.post('/issues/', json={'title': 'inherits', 'initiative': 'Ship the issue tracker'}), status.HTTP_201_CREATED)
    assert created['effective_priority'] == 2
    ok(client.patch(f'{INITIATIVES}Ship the issue tracker/', json={'status': 'completed'}))
    assert ok(client.get(f'/issues/{created["number"]}/'))['effective_priority'] == 0


def test_deleting_an_initiative_keeps_its_issues(client):
    created = ok(client.post('/issues/', json={'title': 'kept', 'initiative': 'Ship the issue tracker'}), status.HTTP_201_CREATED)
    response = client.delete(f'{INITIATIVES}Ship the issue tracker/')
    assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)
    assert ok(client.get(f'/issues/{created["number"]}/'))['initiative'] is None
