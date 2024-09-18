"""Add new 16x16x16 box size.

Revision ID: b03924411cba
Revises: 2f7a9eb3f1cf
Create Date: 2024-09-18 12:46:37.037545
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b03924411cba'
down_revision = '2f7a9eb3f1cf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE boxsize ADD value 'Sixteen' AFTER 'Misc';")


def downgrade() -> None:
    op.execute("ALTER TYPE boxsize RENAME TO boxsizetemp")
    op.execute("CREATE TYPE boxsize as ENUM('Book','Small','Medium','Large','Bag','Monitor','Misc')")
    op.execute("DROP TYPE boxsizetemp")
