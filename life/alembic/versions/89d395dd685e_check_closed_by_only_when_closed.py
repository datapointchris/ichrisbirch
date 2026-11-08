"""check closed_by is null on an open issue

Revision ID: 89d395dd685e
Revises: 816ce25c08dc
Create Date: 2026-10-10 15:37:14.590017

`4ac06e1ade3e` added `closed_by` without this constraint. While that deploy
ran, the outgoing color reopened issues with code that cleared `closed_ts` and
left `closed_by`. Postgres checks every existing row when the constraint is
added, so one such row would fail this migration and the deploy carrying it.
The update clears them first. Nothing is lost: a closer on an open issue names
who closed it before it was reopened, which the API never reports.
"""

from collections.abc import Sequence

from alembic import op

revision: str = '89d395dd685e'
down_revision: str | None = '816ce25c08dc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NAME = 'ck_issues_issue_closed_by_only_when_closed'


def upgrade() -> None:
    op.execute("UPDATE issues SET closed_by = NULL WHERE closed_by IS NOT NULL AND status NOT IN ('completed', 'canceled')")
    op.create_check_constraint(op.f(NAME), 'issues', "closed_by IS NULL OR status IN ('completed', 'canceled')")


def downgrade() -> None:
    op.drop_constraint(op.f(NAME), 'issues', type_='check')
