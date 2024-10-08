"""Add UhaulSmall box to box sizes in box_packing.

Revision ID: 580059210a03
Revises: 0898f6327c22
Create Date: 2024-10-08 04:08:09.119125
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '580059210a03'
down_revision = '0898f6327c22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE boxsize ADD value 'UhaulSmall' AFTER 'Sixteen';")


def downgrade() -> None:
    op.execute('ALTER TYPE boxsize RENAME TO boxsizetemp')
    op.execute("CREATE TYPE boxsize as ENUM('Book','Small','Medium','Large','Bag','Monitor','Misc','Sixteen')")
    op.execute('DROP TYPE boxsizetemp')
