"""Convert project tables to UUID7 PKs, add project description,
add project_item_tasks table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29

"""

import sqlalchemy as sa
from alembic import op

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing project tables in FK order (no production data to preserve)
    op.drop_index('idx_pid_depends', table_name='project_item_dependencies')
    op.drop_index('idx_pid_item', table_name='project_item_dependencies')
    op.drop_table('project_item_dependencies')

    op.drop_index('idx_pim_position', table_name='project_item_memberships')
    op.drop_index('idx_pim_item', table_name='project_item_memberships')
    op.drop_index('idx_pim_project', table_name='project_item_memberships')
    op.drop_table('project_item_memberships')

    op.drop_index('idx_pi_active', table_name='project_items')
    op.drop_table('project_items')

    op.drop_table('projects')

    # Recreate projects with UUID PK and description
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
        sa.UniqueConstraint('name', name=op.f('uq_projects_name')),
    )

    # Recreate project_items with UUID PK
    op.create_table(
        'project_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_items')),
    )
    op.create_index('idx_pi_active', 'project_items', ['archived'], postgresql_where=sa.text('archived = false'))

    # Recreate project_item_memberships with UUID FKs
    op.create_table(
        'project_item_memberships',
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('item_id', 'project_id', name=op.f('pk_project_item_memberships')),
        sa.ForeignKeyConstraint(
            ['item_id'], ['project_items.id'], name=op.f('fk_project_item_memberships_item_id_project_items'), ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'], name=op.f('fk_project_item_memberships_project_id_projects'), ondelete='CASCADE'
        ),
    )
    op.create_index('idx_pim_project', 'project_item_memberships', ['project_id'])
    op.create_index('idx_pim_item', 'project_item_memberships', ['item_id'])
    op.create_index('idx_pim_position', 'project_item_memberships', ['project_id', 'position'])

    # Recreate project_item_dependencies with UUID FKs
    op.create_table(
        'project_item_dependencies',
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('depends_on_id', sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint('item_id', 'depends_on_id', name=op.f('pk_project_item_dependencies')),
        sa.ForeignKeyConstraint(
            ['item_id'], ['project_items.id'], name=op.f('fk_project_item_dependencies_item_id_project_items'), ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['depends_on_id'],
            ['project_items.id'],
            name=op.f('fk_project_item_dependencies_depends_on_id_project_items'),
            ondelete='CASCADE',
        ),
        sa.CheckConstraint('item_id != depends_on_id', name='no_self_dependency'),
        sa.UniqueConstraint('item_id', 'depends_on_id', name=op.f('uq_project_item_dependencies_item_id')),
    )
    op.create_index('idx_pid_item', 'project_item_dependencies', ['item_id'])
    op.create_index('idx_pid_depends', 'project_item_dependencies', ['depends_on_id'])

    # Create new project_item_tasks table
    op.create_table(
        'project_item_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_item_tasks')),
        sa.ForeignKeyConstraint(
            ['item_id'], ['project_items.id'], name=op.f('fk_project_item_tasks_item_id_project_items'), ondelete='CASCADE'
        ),
    )
    op.create_index('idx_pit_item', 'project_item_tasks', ['item_id'])
    op.create_index('idx_pit_position', 'project_item_tasks', ['item_id', 'position'])


def downgrade() -> None:
    # Drop project_item_tasks
    op.drop_index('idx_pit_position', table_name='project_item_tasks')
    op.drop_index('idx_pit_item', table_name='project_item_tasks')
    op.drop_table('project_item_tasks')

    # Drop UUID-based project tables
    op.drop_index('idx_pid_depends', table_name='project_item_dependencies')
    op.drop_index('idx_pid_item', table_name='project_item_dependencies')
    op.drop_table('project_item_dependencies')

    op.drop_index('idx_pim_position', table_name='project_item_memberships')
    op.drop_index('idx_pim_item', table_name='project_item_memberships')
    op.drop_index('idx_pim_project', table_name='project_item_memberships')
    op.drop_table('project_item_memberships')

    op.drop_index('idx_pi_active', table_name='project_items')
    op.drop_table('project_items')

    op.drop_table('projects')

    # Recreate original Integer-based tables (no description field)
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
        sa.UniqueConstraint('name', name=op.f('uq_projects_name')),
    )

    op.create_table(
        'project_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_items')),
    )
    op.create_index('idx_pi_active', 'project_items', ['archived'], postgresql_where=sa.text('archived = false'))

    op.create_table(
        'project_item_memberships',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('item_id', 'project_id', name=op.f('pk_project_item_memberships')),
        sa.ForeignKeyConstraint(
            ['item_id'], ['project_items.id'], name=op.f('fk_project_item_memberships_item_id_project_items'), ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'], name=op.f('fk_project_item_memberships_project_id_projects'), ondelete='CASCADE'
        ),
    )
    op.create_index('idx_pim_project', 'project_item_memberships', ['project_id'])
    op.create_index('idx_pim_item', 'project_item_memberships', ['item_id'])
    op.create_index('idx_pim_position', 'project_item_memberships', ['project_id', 'position'])

    op.create_table(
        'project_item_dependencies',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('depends_on_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('item_id', 'depends_on_id', name=op.f('pk_project_item_dependencies')),
        sa.ForeignKeyConstraint(
            ['item_id'], ['project_items.id'], name=op.f('fk_project_item_dependencies_item_id_project_items'), ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['depends_on_id'],
            ['project_items.id'],
            name=op.f('fk_project_item_dependencies_depends_on_id_project_items'),
            ondelete='CASCADE',
        ),
        sa.CheckConstraint('item_id != depends_on_id', name='no_self_dependency'),
        sa.UniqueConstraint('item_id', 'depends_on_id', name=op.f('uq_project_item_dependencies_item_id')),
    )
    op.create_index('idx_pid_item', 'project_item_dependencies', ['item_id'])
    op.create_index('idx_pid_depends', 'project_item_dependencies', ['depends_on_id'])
