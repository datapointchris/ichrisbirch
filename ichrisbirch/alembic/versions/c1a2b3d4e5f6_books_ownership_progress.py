"""Rename status to ownership, add progress column, drop abandoned

Revision ID: c1a2b3d4e5f6
Revises: b066e197097b
Create Date: 2026-03-15

"""

from alembic import op
import sqlalchemy as sa

revision = 'c1a2b3d4e5f6'
down_revision = 'b066e197097b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create book_progress lookup table
    op.create_table(
        'book_progress',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name'),
    )
    op.execute(
        "INSERT INTO book_progress (name) VALUES "
        "('abandoned'), ('read'), ('reading'), ('unread')"
    )

    # 2. Add progress column with default 'unread'
    op.add_column('books', sa.Column('progress', sa.Text(), server_default='unread', nullable=False))
    op.create_foreign_key('fk_books_progress', 'books', 'book_progress', ['progress'], ['name'])

    # 3. Backfill progress from existing data
    op.execute("""
        UPDATE books SET progress = CASE
            WHEN abandoned = TRUE THEN 'abandoned'
            WHEN read_finish_date IS NOT NULL THEN 'read'
            WHEN read_start_date IS NOT NULL THEN 'reading'
            ELSE 'unread'
        END
    """)

    # 4. Rename 'skipped' to 'rejected': add new value, migrate data, remove old value
    op.execute("INSERT INTO book_statuses (name) VALUES ('rejected') ON CONFLICT DO NOTHING")
    op.execute("UPDATE books SET status = 'rejected' WHERE status = 'skipped'")
    op.execute("DELETE FROM book_statuses WHERE name = 'skipped'")

    # 5. Rename book_statuses table to book_ownership
    op.rename_table('book_statuses', 'book_ownership')

    # 6. Rename status column to ownership
    op.alter_column('books', 'status', new_column_name='ownership')

    # 7. Rename skip_reason to reject_reason
    op.alter_column('books', 'skip_reason', new_column_name='reject_reason')

    # 8. Drop abandoned column
    op.drop_column('books', 'abandoned')


def downgrade() -> None:
    # 1. Re-add abandoned column
    op.add_column('books', sa.Column('abandoned', sa.Boolean(), nullable=True))

    # 2. Backfill abandoned from progress
    op.execute("UPDATE books SET abandoned = TRUE WHERE progress = 'abandoned'")

    # 3. Rename reject_reason back to skip_reason
    op.alter_column('books', 'reject_reason', new_column_name='skip_reason')

    # 4. Rename ownership back to status
    op.alter_column('books', 'ownership', new_column_name='status')

    # 5. Rename book_ownership back to book_statuses
    op.rename_table('book_ownership', 'book_statuses')

    # 6. Rename 'rejected' back to 'skipped': add old value, migrate data, remove new value
    op.execute("INSERT INTO book_statuses (name) VALUES ('skipped') ON CONFLICT DO NOTHING")
    op.execute("UPDATE books SET status = 'skipped' WHERE status = 'rejected'")
    op.execute("DELETE FROM book_statuses WHERE name = 'rejected'")

    # 7. Drop progress FK and column
    op.drop_constraint('fk_books_progress', 'books', type_='foreignkey')
    op.drop_column('books', 'progress')

    # 8. Drop book_progress table
    op.drop_table('book_progress')
