"""add book status lookup table and skip reason

Revision ID: b066e197097b
Revises: e010f859f025
Create Date: 2026-03-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'b066e197097b'
down_revision: str | None = 'e010f859f025'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'book_statuses',
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('name', name=op.f('pk_book_statuses')),
    )
    op.execute(
        "INSERT INTO book_statuses (name) VALUES "
        "('donated'), ('owned'), ('skipped'), ('sold'), ('to_purchase')"
    )
    op.add_column('books', sa.Column('status', sa.Text(), server_default='owned', nullable=False))
    op.create_foreign_key(op.f('fk_books_status_book_statuses'), 'books', 'book_statuses', ['status'], ['name'])
    op.add_column('books', sa.Column('skip_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('books', 'skip_reason')
    op.drop_constraint(op.f('fk_books_status_book_statuses'), 'books', type_='foreignkey')
    op.drop_column('books', 'status')
    op.drop_table('book_statuses')
