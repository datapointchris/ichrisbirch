"""Add Personal and Kitchen to taskcategory enum.

Revision ID: 0898f6327c22
Revises: b03924411cba
Create Date: 2024-09-18 23:35:32.902213
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '0898f6327c22'
down_revision = 'b03924411cba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE taskcategory ADD value 'Personal' BEFORE 'Automotive';")
    op.execute("ALTER TYPE taskcategory ADD value 'Kitchen' AFTER 'Home';")


def downgrade() -> None:
    op.execute("ALTER TYPE taskcategory RENAME TO taskcategorytemp")
    op.execute(
        "CREATE TYPE taskcategory as "
        + "ENUM('Automotive','Chore','Computer','Dingo','Financial','Home','Learn','Purchase','Research','Work')",
    )
    op.execute("DROP TYPE taskcategorytemp")
