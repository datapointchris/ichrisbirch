"""Add issues: software work tracked apart from personal projects

Issues are written for the agent that does the work. Each carries an acceptance
check, a coarse priority, a float rank, a claim with an expiry, a deferral day,
and three kinds of edge: a dependency that gates readiness, a parent that groups
children, and provenance links for discovered and duplicate work. Initiatives
are the bounded outcomes issues may belong to, and labels are a closed
vocabulary with exclusive groups.

Project items and issues draw their numbers from one sequence, `item_numbers`,
so a bare number names one row across both tables. The sequence starts above
every number already issued: the highest item number, and the identity's own
counter, which also counts items since deleted. The identity on
`project_items.number` is replaced by a default drawing from the sequence. The
release serving while this runs inserts items without a number, so the default
answers it the same way the identity did.

Projects gain `someday`, a status that is neither active nor terminal.

This creates tables and moves no rows.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op

revision = 'c8d9e0f1a2b3'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None

SLUG_PATTERN = '^[a-z0-9]+(-[a-z0-9]+)*$'


def upgrade() -> None:
    op.execute("INSERT INTO project_statuses (name) VALUES ('someday')")

    op.execute('CREATE SEQUENCE item_numbers AS bigint')
    op.execute("""
        DO $$
        DECLARE
            identity_sequence text := pg_get_serial_sequence('project_items', 'number');
            identity_issued bigint := 0;
            highest bigint;
        BEGIN
            IF identity_sequence IS NOT NULL THEN
                EXECUTE format(
                    'SELECT CASE WHEN is_called THEN last_value ELSE last_value - 1 END FROM %s',
                    identity_sequence
                ) INTO identity_issued;
            END IF;
            SELECT COALESCE(MAX(number), 0) INTO highest FROM project_items;
            PERFORM setval('item_numbers', GREATEST(identity_issued, highest) + 1, false);
        END $$;
    """)
    op.execute('ALTER TABLE project_items ALTER COLUMN number DROP IDENTITY IF EXISTS')
    op.execute("ALTER TABLE project_items ALTER COLUMN number SET DEFAULT nextval('item_numbers')")

    op.create_table('issue_statuses', sa.Column('name', sa.Text(), primary_key=True))
    op.execute(
        "INSERT INTO issue_statuses (name) VALUES ('triage'), ('open'), ('in_progress'), ('completed'), ('canceled')"
    )
    op.create_table('issue_types', sa.Column('name', sa.Text(), primary_key=True))
    op.execute("INSERT INTO issue_types (name) VALUES ('bug'), ('feature'), ('task'), ('chore'), ('decision')")
    op.create_table('initiative_statuses', sa.Column('name', sa.Text(), primary_key=True))
    op.execute("INSERT INTO initiative_statuses (name) VALUES ('active'), ('completed'), ('dropped')")

    op.create_table(
        'initiatives',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status', sa.Text(), sa.ForeignKey('initiative_statuses.name'), nullable=False, server_default='active'
        ),
        sa.Column('status_reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('closed_ts', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status <> 'dropped' OR status_reason IS NOT NULL", name='initiative_dropped_requires_reason'
        ),
        sa.CheckConstraint('priority BETWEEN 0 AND 4', name='initiative_priority_range'),
    )
    op.create_index(
        'uq_initiatives_name_active', 'initiatives', ['name'], unique=True, postgresql_where=sa.text("status = 'active'")
    )

    op.create_table(
        'issues',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column(
            'number', sa.BigInteger(), nullable=False, server_default=sa.text("nextval('item_numbers')"), unique=True
        ),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('acceptance', sa.Text(), nullable=True),
        sa.Column('repo', sa.Text(), nullable=True),
        sa.Column('type', sa.Text(), sa.ForeignKey('issue_types.name'), nullable=False, server_default='task'),
        sa.Column('status', sa.Text(), sa.ForeignKey('issue_statuses.name'), nullable=False, server_default='open'),
        sa.Column('status_reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('rank', sa.Double(), nullable=False),
        sa.Column('deferred_until_date', sa.Date(), nullable=True),
        sa.Column('claimed_by', sa.Text(), nullable=True),
        sa.Column('claim_expires_ts', sa.DateTime(timezone=True), nullable=True),
        sa.Column('initiative_id', sa.Uuid(), sa.ForeignKey('initiatives.id', ondelete='SET NULL'), nullable=True),
        sa.Column('parent_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='SET NULL'), nullable=True),
        sa.Column('discovered_from_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='SET NULL'), nullable=True),
        sa.Column('duplicate_of_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('closed_ts', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('priority BETWEEN 0 AND 4', name='issue_priority_range'),
        sa.CheckConstraint(
            "status <> 'canceled' OR status_reason IS NOT NULL OR duplicate_of_id IS NOT NULL",
            name='issue_canceled_requires_reason',
        ),
        sa.CheckConstraint("status_reason IS NULL OR status = 'canceled'", name='issue_reason_only_when_canceled'),
        sa.CheckConstraint('(claimed_by IS NULL) = (claim_expires_ts IS NULL)', name='issue_claim_is_whole'),
        sa.CheckConstraint("claimed_by IS NULL OR status = 'in_progress'", name='issue_claim_only_in_progress'),
        sa.CheckConstraint(
            "closed_ts IS NULL OR status IN ('completed', 'canceled')", name='issue_closed_ts_only_when_closed'
        ),
        sa.CheckConstraint(
            "duplicate_of_id IS NULL OR status = 'canceled'", name='issue_duplicate_only_when_canceled'
        ),
        sa.CheckConstraint('parent_id IS NULL OR parent_id <> id', name='issue_not_own_parent'),
        sa.CheckConstraint(
            'discovered_from_id IS NULL OR discovered_from_id <> id', name='issue_not_discovered_from_itself'
        ),
        sa.CheckConstraint('duplicate_of_id IS NULL OR duplicate_of_id <> id', name='issue_not_duplicate_of_itself'),
    )
    op.create_index('ix_issues_repo', 'issues', ['repo'])
    op.create_index('ix_issues_initiative_id', 'issues', ['initiative_id'])
    op.create_index('ix_issues_parent_id', 'issues', ['parent_id'])
    op.create_index('idx_issues_status', 'issues', ['status'])
    op.create_index('idx_issues_rank', 'issues', ['rank'])

    op.create_table(
        'issue_dependencies',
        sa.Column('issue_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('depends_on_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='CASCADE'), primary_key=True),
        sa.CheckConstraint('issue_id <> depends_on_id', name='issue_no_self_dependency'),
    )
    op.create_index('idx_issue_dependencies_depends_on', 'issue_dependencies', ['depends_on_id'])

    op.create_table(
        'issue_labels',
        sa.Column('id', sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column('slug', sa.Text(), nullable=False, unique=True),
        sa.Column('group_slug', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.CheckConstraint(f"slug ~ '{SLUG_PATTERN}'", name='issue_label_slug_shape'),
        sa.CheckConstraint(
            f"group_slug IS NULL OR group_slug ~ '{SLUG_PATTERN}'", name='issue_label_group_slug_shape'
        ),
    )

    op.create_table(
        'issue_label_assignments',
        sa.Column('issue_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('label_id', sa.Integer(), sa.ForeignKey('issue_labels.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('idx_issue_label_assignments_label', 'issue_label_assignments', ['label_id'])

    op.create_table(
        'issue_comments',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('issue_id', sa.Uuid(), sa.ForeignKey('issues.id', ondelete='CASCADE'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('created_ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_issue_comments_issue_id', 'issue_comments', ['issue_id'])


def downgrade() -> None:
    op.drop_table('issue_comments')
    op.drop_table('issue_label_assignments')
    op.drop_table('issue_labels')
    op.drop_table('issue_dependencies')
    op.drop_table('issues')
    op.drop_table('initiatives')
    op.drop_table('initiative_statuses')
    op.drop_table('issue_types')
    op.drop_table('issue_statuses')

    # The identity restarts above the sequence's counter, not just the highest
    # item. Otherwise it would issue again the numbers the dropped issues held.
    op.execute('ALTER TABLE project_items ALTER COLUMN number DROP DEFAULT')
    op.execute("""
        DO $$
        DECLARE
            sequence_issued bigint;
            next_number bigint;
        BEGIN
            SELECT CASE WHEN is_called THEN last_value ELSE last_value - 1 END INTO sequence_issued FROM item_numbers;
            SELECT GREATEST(COALESCE(MAX(number), 0), sequence_issued) + 1 INTO next_number FROM project_items;
            EXECUTE format(
                'ALTER TABLE project_items ALTER COLUMN number ADD GENERATED BY DEFAULT AS IDENTITY (RESTART %s)',
                next_number
            );
        END $$;
    """)
    op.execute('DROP SEQUENCE item_numbers')

    # `someday` does not exist below this revision. A someday project becomes
    # active, the status that keeps it in view.
    op.execute("UPDATE projects SET status = 'active' WHERE status = 'someday'")
    op.execute("DELETE FROM project_statuses WHERE name = 'someday'")
