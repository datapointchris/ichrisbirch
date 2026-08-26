"""Drop the chat schema

`chat.chats` and `chat.messages` hold two tables no code can reach. The chat UI
runs as its own service on a separate host, and nothing in this repo has read
either table since the Streamlit app and its `/chat` routes were removed.

The downgrade recreates nothing. The stored conversations are not carried to
the replacement service and no export was taken, so an empty pair of tables
would restore the shape without the content and read as a working rollback.

This is destructive and it runs above the deploy's verification gate.
`scripts/deploy-homelab.sh` calls `run_migrations`, then `run_smoke_tests`, and
prints `POINT OF NO RETURN` below both — so a smoke failure tears down the
deploy color and leaves the previous release serving, with the tables already
gone. That ordering is unchanged. What makes this safe is that no running color
reads the tables: a successful deploy removes the old color, so only one color
serves at a time, and that color has carried no chat code since the removal
shipped.

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
    pass
