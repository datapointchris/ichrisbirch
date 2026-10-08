"""Default a project's kind to life

Development work is an issue, so a project created without a kind is personal.
The release serving while this runs sends its own default of `build` on every
create, so the column default reaches only a writer that names no kind.

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
