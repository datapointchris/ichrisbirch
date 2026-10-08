"""Rank placement against a real table, since every move reads its neighbors from it."""

import pytest
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.services.issue_rank import MIN_GAP
from ichrisbirch.services.issue_rank import move_issue


@pytest.fixture
def session(txn_api):
    _, session = txn_api
    return session


def place(session, *ranks: float) -> list[models.Issue]:
    issues = [models.Issue(title=f'ranked {rank}', rank=rank) for rank in ranks]
    session.add_all(issues)
    session.flush()
    return issues


def order(session) -> list[str]:
    return list(session.scalars(select(models.Issue.title).order_by(models.Issue.rank)).all())


def test_a_spent_gap_renumbers_every_rank_and_keeps_the_order(session):
    tight = 1.0 + MIN_GAP / 4
    first, second, mover = place(session, 1.0, tight, 5.0)
    move_issue(session, mover, after=first)
    session.flush()

    assert order(session) == ['ranked 1.0', 'ranked 5.0', f'ranked {tight}']
    assert (first.rank, mover.rank, second.rank) == (1.0, 1.5, 2.0)
