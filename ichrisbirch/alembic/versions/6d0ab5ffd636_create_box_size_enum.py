"""Create box size enum.

Revision ID: 6d0ab5ffd636
Revises: 74af91565f9a
Create Date: 2024-02-24 21:14:01.681253
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '6d0ab5ffd636'
down_revision = '74af91565f9a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE boxsize as ENUM('Book', 'Small', 'Medium', 'Large', 'Bag', 'Monitor', 'Misc')")
    op.execute("ALTER TABLE box_packing.boxes ALTER COLUMN SIZE TYPE boxsize USING SIZE::boxsize")


def downgrade() -> None:
    op.execute("ALTER TABLE box_packing.boxes ALTER COLUMN SIZE TYPE VARCHAR USING SIZE::VARCHAR")
    op.execute("DROP TYPE boxsize")
