"""add closed_by to issues

Revision ID: 4ac06e1ade3e
Revises: 04106ba80f02
Create Date: 2026-10-10 14:24:09.630027

Every issue closed before this column existed keeps a null `closed_by`, which
reads as unknown. Nothing on those rows says who closed them, so nothing is
backfilled.

The CHECK keeping `closed_by` null on an open issue waits for a later
revision. During a deploy the outgoing color reopens an issue without clearing
this column, and the constraint would refuse that write. Those reopened rows
are why that revision clears `closed_by` on every open issue before it adds
the constraint.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '4ac06e1ade3e'
down_revision: str | None = '04106ba80f02'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('issues', sa.Column('closed_by', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'closed_by')
