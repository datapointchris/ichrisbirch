"""Change TaskFrequency to AutoTaskFrequency.

Revision ID: d2922c54fe22
Revises: 3170c2adb2bb
Create Date: 2024-05-10 08:35:41.927726
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd2922c54fe22'
down_revision = '3170c2adb2bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE AutoTaskFrequency AS ENUM "
        "('Daily', 'Weekly', 'Biweekly', 'Monthly', 'Quarterly', 'Semiannually', 'Yearly')"
    )
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE TEXT USING frequency::TEXT")
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE AutoTaskFrequency USING frequency::AutoTaskFrequency")


def downgrade() -> None:
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE TEXT USING frequency::TEXT")
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE TaskFrequency USING frequency::TaskFrequency")
