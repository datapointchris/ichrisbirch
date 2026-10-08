"""Default a project's kind to life

Development work is an issue, so a project created without a kind is personal.
The API's create schema fills in its own default before the insert, so this
column default reaches only a writer naming no kind. A project created through
the release still serving while this runs gets that release's `build`.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-10-08

"""

from alembic import op

revision = 'e0f1a2b3c4d5'
down_revision = 'd9e0f1a2b3c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE projects ALTER COLUMN kind SET DEFAULT 'life'")


def downgrade() -> None:
    op.execute("ALTER TABLE projects ALTER COLUMN kind SET DEFAULT 'build'")
