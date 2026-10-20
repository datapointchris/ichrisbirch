"""add someday initiative status

Revision ID: 042e45a86222
Revises: 51cd77742134
Create Date: 2026-10-19 21:00:00.000000

Initiatives gain `someday`, a status that is neither active nor terminal, as
projects have. A someday initiative holds ideas not yet taken on, and none of
its issues is ready.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '042e45a86222'
down_revision = '51cd77742134'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("INSERT INTO initiative_statuses (name) VALUES ('someday')")


def downgrade() -> None:
    # `someday` does not exist below this revision. A someday initiative becomes
    # active again, the nearest status that keeps its issues open.
    op.execute("UPDATE initiatives SET status = 'active' WHERE status = 'someday'")
    op.execute("DELETE FROM initiative_statuses WHERE name = 'someday'")
