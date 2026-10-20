"""number initiatives from the item sequence

Revision ID: 7e7af73fb30a
Revises: 042e45a86222
Create Date: 2026-10-20 15:04:48.995881

An initiative gains a number drawn from `item_numbers`, the sequence issues and
project items already share, so a bare number names one row across all three.
Existing initiatives are numbered in the order they were created. The column
takes its default before it becomes NOT NULL, so the release serving while this
runs inserts initiatives that are numbered too.
"""

import sqlalchemy as sa
from alembic import op

revision = '7e7af73fb30a'
down_revision = '042e45a86222'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('initiatives', sa.Column('number', sa.BigInteger(), nullable=True))
    op.execute("ALTER TABLE initiatives ALTER COLUMN number SET DEFAULT nextval('item_numbers')")
    op.execute(
        """
        DO $$
        DECLARE
            initiative record;
        BEGIN
            FOR initiative IN SELECT id FROM initiatives WHERE number IS NULL ORDER BY created_ts, id LOOP
                UPDATE initiatives SET number = nextval('item_numbers') WHERE id = initiative.id;
            END LOOP;
        END $$;
        """
    )
    op.alter_column('initiatives', 'number', nullable=False)
    op.create_unique_constraint(op.f('uq_initiatives_number'), 'initiatives', ['number'])


def downgrade() -> None:
    op.drop_constraint(op.f('uq_initiatives_number'), 'initiatives', type_='unique')
    op.drop_column('initiatives', 'number')
