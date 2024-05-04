"""Add Personal to TaskCategory

Revision ID: ab313adc94b9
Revises: 3170c2adb2bb
Create Date: 2024-05-04 01:59:26.657653

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ab313adc94b9'
down_revision = '3170c2adb2bb'
branch_labels = None
depends_on = None

new = (
    "('Automotive', 'Chore', 'Computer', 'Dingo', 'Financial', 'Home', "
    "'Kitchen', 'Learn', 'Personal', 'Purchase', 'Research', 'Work')"
)
old = (
    "('Automotive', 'Chore', 'Computer', 'Dingo', 'Financial', 'Home', "
    "'Kitchen', 'Learn', 'Purchase', 'Research', 'Work')"
)


def upgrade() -> None:
    op.execute("ALTER TYPE TaskCategory RENAME TO TaskCategoryTemp")
    op.execute(f"CREATE TYPE TaskCategory as ENUM{new}")
    op.execute("ALTER TABLE tasks ALTER COLUMN category TYPE TaskCategory USING category::text::TaskCategory")
    op.execute("DROP TYPE TaskCategoryTemp CASCADE")


def downgrade() -> None:
    op.execute("ALTER TYPE TaskCategory RENAME TO TaskCategoryTemp")
    op.execute(f"CREATE TYPE TaskCategory as ENUM{old}")
    op.execute("ALTER TABLE tasks ALTER COLUMN category TYPE TaskCategory USING category::text::TaskCategory")
    op.execute("DROP TYPE TaskCategoryTemp CASCADE")
