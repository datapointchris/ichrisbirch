"""collapse whitespace in article titles

Titles saved by an earlier importer kept the source page's newlines, tabs and
indentation, so they printed across several lines and sorted ahead of every
letter. Every run of whitespace becomes one space and the ends are trimmed,
which is what `OneLineText` does to a title on its way in.

Revision ID: a0c4a2393384
Revises: 2475f04ad042
Create Date: 2026-10-10 17:59:01.113448

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a0c4a2393384'
down_revision = '2475f04ad042'
branch_labels = None
depends_on = None

# What str.split() splits on; [[:space:]] alone misses the no-break space.
WHITESPACE = r'[[:space:]\u001c-\u001f\u0085   -     　]'
COLLAPSED = f"btrim(regexp_replace(title, '{WHITESPACE}+', ' ', 'g'))"


def upgrade() -> None:
    op.execute(f'UPDATE articles SET title = {COLLAPSED} WHERE title <> {COLLAPSED}')


def downgrade() -> None:
    # The removed whitespace carried nothing, and a second upgrade changes no row.
    pass
