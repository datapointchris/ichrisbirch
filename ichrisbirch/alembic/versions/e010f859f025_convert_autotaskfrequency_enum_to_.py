"""convert AutoTaskFrequency enum to lookup table

Revision ID: e010f859f025
Revises: d28489933781
Create Date: 2026-03-13 23:57:06.574147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e010f859f025'
down_revision = 'd28489933781'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create lookup table
    op.create_table(
        'autotask_frequencies',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_autotask_frequencies')),
    )

    # Step 2: Insert valid frequency values
    op.execute(
        "INSERT INTO autotask_frequencies (name) VALUES "
        "('Biweekly'), ('Daily'), ('Monthly'), ('Quarterly'), "
        "('Semiannually'), ('Weekly'), ('Yearly')"
    )

    # Step 3: Convert ENUM column to TEXT
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE TEXT USING frequency::text")

    # Step 4: Add FK constraint
    op.create_foreign_key(
        op.f('fk_autotasks_frequency_autotask_frequencies'),
        'autotasks', 'autotask_frequencies',
        ['frequency'], ['name'],
    )

    # Step 5: Drop the PostgreSQL ENUM type
    op.execute("DROP TYPE autotaskfrequency")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE autotaskfrequency AS ENUM "
        "('Biweekly', 'Daily', 'Monthly', 'Quarterly', 'Semiannually', 'Weekly', 'Yearly')"
    )
    op.drop_constraint(op.f('fk_autotasks_frequency_autotask_frequencies'), 'autotasks', type_='foreignkey')
    op.execute("ALTER TABLE autotasks ALTER COLUMN frequency TYPE autotaskfrequency USING frequency::autotaskfrequency")
    op.drop_table('autotask_frequencies')
