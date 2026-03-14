"""convert TaskCategory enum to lookup table

Revision ID: 147500c3d0b3
Revises: 8e4ce2fcf9cd
Create Date: 2026-03-13 23:12:16.637130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '147500c3d0b3'
down_revision = '8e4ce2fcf9cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create the lookup table — must exist before we can insert or FK to it
    op.create_table(
        'task_categories',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_task_categories')),
    )

    # Step 2: Insert valid category values — must exist before FK constraints
    # are added, otherwise existing data would violate the constraint
    op.execute(
        "INSERT INTO task_categories (name) VALUES "
        "('Automotive'), ('Chore'), ('Computer'), ('Dingo'), ('Financial'), "
        "('Home'), ('Kitchen'), ('Learn'), ('Personal'), ('Purchase'), "
        "('Research'), ('Work')"
    )

    # Step 3: Convert ENUM columns to TEXT — must happen before adding FK
    # constraints (can't FK from ENUM to TEXT) and before dropping the ENUM type
    # USING category::text tells PostgreSQL how to cast existing ENUM values to text
    op.execute("ALTER TABLE tasks ALTER COLUMN category TYPE TEXT USING category::text")
    op.execute("ALTER TABLE autotasks ALTER COLUMN category TYPE TEXT USING category::text")

    # Step 4: Add FK constraints — lookup table has data, columns are TEXT,
    # so existing values will validate against the lookup table
    op.create_foreign_key(
        op.f('fk_tasks_category_task_categories'),
        'tasks', 'task_categories',
        ['category'], ['name'],
    )
    op.create_foreign_key(
        op.f('fk_autotasks_category_task_categories'),
        'autotasks', 'task_categories',
        ['category'], ['name'],
    )

    # Step 5: Drop the PostgreSQL ENUM type — no columns reference it anymore
    op.execute("DROP TYPE taskcategory")


def downgrade() -> None:
    # Reverse: recreate ENUM, convert back, drop FK and lookup table
    op.execute(
        "CREATE TYPE taskcategory AS ENUM "
        "('Automotive', 'Chore', 'Computer', 'Dingo', 'Financial', "
        "'Home', 'Kitchen', 'Learn', 'Personal', 'Purchase', 'Research', 'Work')"
    )
    op.drop_constraint(op.f('fk_autotasks_category_task_categories'), 'autotasks', type_='foreignkey')
    op.drop_constraint(op.f('fk_tasks_category_task_categories'), 'tasks', type_='foreignkey')
    op.execute("ALTER TABLE tasks ALTER COLUMN category TYPE taskcategory USING category::taskcategory")
    op.execute("ALTER TABLE autotasks ALTER COLUMN category TYPE taskcategory USING category::taskcategory")
    op.drop_table('task_categories')
