"""Tests for the issues seeder."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import pytest

from ichrisbirch.models.issue import INITIATIVE_STATUSES
from ichrisbirch.models.issue import ISSUE_STATUSES
from ichrisbirch.models.issue import ISSUE_TYPES
from ichrisbirch.models.issue import Initiative
from ichrisbirch.models.issue import Issue
from ichrisbirch.services.issue_readiness import measure_readiness
from scripts.seed.seeders import issues

pytestmark = [pytest.mark.seed, pytest.mark.integration]


@pytest.fixture
def seeded(db):
    issues.clear(db)
    issues.seed(db, scale=1)
    now = datetime.now(UTC)
    return db, measure_readiness(db, now.date(), now)


def by_title(db, title: str) -> Issue:
    return db.query(Issue).filter(Issue.title == title).one()


class TestIssueSeeder:
    def test_every_vocabulary_value_is_represented(self, seeded):
        """A status or type with no seeded issue cannot be exercised in the UI or a filtered read."""
        db, _ = seeded
        assert {issue.status for issue in db.query(Issue).all()} == set(ISSUE_STATUSES)
        assert {issue.type for issue in db.query(Issue).all()} == set(ISSUE_TYPES)
        assert {initiative.status for initiative in db.query(Initiative).all()} == set(INITIATIVE_STATUSES)

    def test_closed_stamps_match_status(self, seeded):
        db, _ = seeded
        for issue in db.query(Issue).all():
            assert (issue.closed_ts is not None) == issue.is_closed, f'#{issue.number} disagrees with its own status'

    def test_an_expired_claim_is_ready_and_a_live_one_is_not(self, seeded):
        db, readiness = seeded
        assert by_title(db, 'Issue list filters by label').id in readiness.ready
        assert by_title(db, 'icb issues next prints the claimed issue').id not in readiness.ready

    def test_a_blocked_issue_and_a_waiting_parent_are_present(self, seeded):
        db, readiness = seeded
        blocked = by_title(db, 'Routing file misses the issues paths')
        fan_in = by_title(db, 'Port overview to the issues section')
        parent = by_title(db, 'Initiative board page')
        assert blocked.id in readiness.blocked
        assert len(fan_in.dependencies) == 2
        assert parent.id not in readiness.ready
        assert readiness.open_child_count[parent.id] == 1

    def test_a_low_priority_blocker_inherits_the_urgency_it_gates(self, seeded):
        db, readiness = seeded
        blocker = by_title(db, 'Rank renumbers when the gap is spent')
        assert blocker.priority == 4
        assert readiness.effective_priority[blocker.id] == 1

    def test_a_deferred_issue_waits_for_its_day(self, seeded):
        db, readiness = seeded
        deferred = by_title(db, 'Comment thread on issue detail')
        assert deferred.deferred_until_date is not None
        assert deferred.id not in readiness.blocked
        assert deferred.id not in readiness.ready
