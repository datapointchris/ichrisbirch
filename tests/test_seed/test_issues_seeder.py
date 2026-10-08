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

    def test_every_readiness_state_is_represented(self, seeded):
        """A state no seeded issue is in cannot be seen on the page or reached through a lens."""
        db, readiness = seeded
        now = datetime.now(UTC)
        rows = db.query(Issue).all()
        states = {
            'ready': any(issue.id in readiness.ready for issue in rows),
            'blocked': any(issue.id in readiness.blocked for issue in rows),
            'deferred, neither blocked nor ready': any(
                issue.id in readiness.deferred and issue.id not in readiness.blocked and issue.id not in readiness.ready for issue in rows
            ),
            'claimed': any(issue.claim_expires_ts is not None and issue.claim_expires_ts > now for issue in rows),
            'a parent with an open child': any(readiness.open_child_count.get(issue.id) for issue in rows),
        }
        assert [state for state, present in states.items() if not present] == []
