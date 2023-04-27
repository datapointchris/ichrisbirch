"""Add Purchase, Work, Kitchen to ENUM values for TaskCategory

Revision ID: 0bc20d6a3ae1
Revises: fc2932fa2d10
Create Date: 2023-04-26 19:32:09.826042

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0bc20d6a3ae1'
down_revision = 'fc2932fa2d10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE taskcategory ADD value 'Work' AFTER 'Home';")
    op.execute("ALTER TYPE taskcategory ADD value 'Work' AFTER 'Home';")
    op.execute("ALTER TYPE taskcategory ADD value 'Work' AFTER 'Home';")


def downgrade() -> None:
    op.execute("ALTER TYPE taskcategory RENAME TO taskcategorytemp")
    op.execute("CREATE TYPE taskcategory as ENUM('Home','Chore','Dingo','Learn','Research','Computer','Financial')")
    op.execute("DROP TYPE taskcategorytmp")
