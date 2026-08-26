"""Drop the chat schema

`chat.chats` and `chat.messages` hold two tables nothing in this repo reads.

There is no way back. The rows are not carried anywhere and no export was
taken, so recovery is a database backup taken before this ran.

This is destructive and it runs above the deploy's verification gate.
`scripts/deploy-homelab.sh` calls `run_migrations`, then `run_smoke_tests`, and
prints `POINT OF NO RETURN` below both, so a smoke failure tears down the
deploy color and leaves the previous release serving with the tables already
gone. What makes that survivable is that no running color reads the tables: a
successful deploy removes the old color, so one color serves at a time.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-26

"""

from alembic import op

revision = 'd3e4f5a6b7c8'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # messages carries the foreign key, so it goes first.
    op.drop_table('messages', schema='chat')
    op.drop_table('chats', schema='chat')
    op.execute('DROP SCHEMA IF EXISTS chat')


def downgrade() -> None:
    # Refuse here rather than let the next `upgrade head` fail. A `pass` lets
    # alembic stamp c2d3e4f5a6b7 over a database whose chat schema is already
    # gone, and the re-upgrade then dies on `drop_table` with nothing to drop —
    # stuck below head with no way forward. Failing now leaves the database
    # consistent and at head.
    raise NotImplementedError(
        'd3e4f5a6b7c8 drops the chat schema and its rows. There is no downgrade — '
        'restore from a database backup taken before it ran.'
    )
