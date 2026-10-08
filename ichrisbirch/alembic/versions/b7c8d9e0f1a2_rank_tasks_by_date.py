"""Rank open tasks by a sort date instead of a positional priority

A task gets `rank_at`, the moment it should reach the top of the list, set to
its add date plus its window. `window_days` comes from the task's category,
which gains its own `window_days`. A task can be pinned, and dropped as well as
completed. A copy made by an autotask records which template made it.

`tasks.priority` and `autotasks.priority` stay, nullable, holding the ranks
they had. Nothing writes them after this.

Every new NOT NULL column has a constant server default, because the release
serving while this runs inserts tasks without them.

Existing copies are linked to their template by exact name, which is the only
link the schema had. A one-off task sharing a template's name is linked too.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op

revision = 'b7c8d9e0f1a2'
down_revision = 'a6b7c8d9e0f1'
branch_labels = None
depends_on = None

CATEGORY_WINDOW_DAYS = {
    'Automotive': 45,
    'Chore': 30,
    'Computer': 90,
    'Dingo': 7,
    'Financial': 30,
    'Home': 60,
    'Kitchen': 30,
    'Learn': 180,
    'Personal': 60,
    'Purchase': 30,
    'Research': 180,
    'Work': 60,
}


def upgrade() -> None:
    op.create_table('autotask_anchors', sa.Column('name', sa.Text(), primary_key=True))
    op.execute("INSERT INTO autotask_anchors (name) VALUES ('calendar'), ('completion')")

    op.add_column('task_categories', sa.Column('window_days', sa.Integer(), nullable=False, server_default=sa.text('60')))
    for name, window_days in CATEGORY_WINDOW_DAYS.items():
        op.execute(
            sa.text('UPDATE task_categories SET window_days = :window_days WHERE name = :name').bindparams(
                name=name, window_days=window_days
            )
        )
    op.create_check_constraint('window_days_positive', 'task_categories', 'window_days >= 1')

    op.alter_column('autotasks', 'priority', existing_type=sa.Integer(), nullable=True)
    op.add_column('autotasks', sa.Column('window_days', sa.Integer(), nullable=True))
    op.add_column(
        'autotasks',
        sa.Column('anchor', sa.Text(), sa.ForeignKey('autotask_anchors.name'), nullable=False, server_default='completion'),
    )
    op.create_check_constraint('window_days_positive', 'autotasks', 'window_days IS NULL OR window_days >= 1')

    op.alter_column('tasks', 'priority', existing_type=sa.Integer(), nullable=True)
    op.add_column(
        'tasks',
        sa.Column('rank_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now() + interval '30 days'")),
    )
    op.add_column('tasks', sa.Column('window_days', sa.Integer(), nullable=False, server_default=sa.text('30')))
    op.add_column('tasks', sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column(
        'tasks',
        sa.Column('autotask_id', sa.Integer(), sa.ForeignKey('autotasks.id', ondelete='SET NULL'), nullable=True),
    )
    op.add_column('tasks', sa.Column('drop_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('drop_reason', sa.Text(), nullable=True))
    op.create_check_constraint('window_days_positive', 'tasks', 'window_days >= 1')
    op.create_check_constraint('one_closed_state', 'tasks', 'complete_date IS NULL OR drop_date IS NULL')

    op.execute(
        """
        UPDATE tasks
        SET autotask_id = templates.id
        FROM (SELECT DISTINCT ON (name) id, name FROM autotasks ORDER BY name, id) AS templates
        WHERE tasks.name = templates.name
        """
    )
    op.execute(
        """
        UPDATE tasks
        SET window_days = task_categories.window_days,
            rank_at = tasks.add_date + make_interval(days => task_categories.window_days),
            pinned = (tasks.priority IS NOT NULL AND tasks.priority <= 0 AND tasks.complete_date IS NULL)
        FROM task_categories
        WHERE tasks.category = task_categories.name
        """
    )
    op.create_check_constraint('pinned_only_open', 'tasks', 'NOT pinned OR (complete_date IS NULL AND drop_date IS NULL)')
    op.create_check_constraint('drop_reason_needs_drop_date', 'tasks', 'drop_reason IS NULL OR drop_date IS NOT NULL')


def downgrade() -> None:
    op.execute('UPDATE tasks SET priority = 1 WHERE priority IS NULL')
    op.drop_constraint('drop_reason_needs_drop_date', 'tasks', type_='check')
    op.drop_constraint('pinned_only_open', 'tasks', type_='check')
    op.drop_constraint('one_closed_state', 'tasks', type_='check')
    op.drop_constraint('window_days_positive', 'tasks', type_='check')
    for column in ('drop_reason', 'drop_date', 'autotask_id', 'pinned', 'window_days', 'rank_at'):
        op.drop_column('tasks', column)
    op.alter_column('tasks', 'priority', existing_type=sa.Integer(), nullable=False)

    op.execute('UPDATE autotasks SET priority = 1 WHERE priority IS NULL')
    op.drop_constraint('window_days_positive', 'autotasks', type_='check')
    op.drop_column('autotasks', 'anchor')
    op.drop_column('autotasks', 'window_days')
    op.alter_column('autotasks', 'priority', existing_type=sa.Integer(), nullable=False)

    op.drop_constraint('window_days_positive', 'task_categories', type_='check')
    op.drop_column('task_categories', 'window_days')
    op.drop_table('autotask_anchors')
