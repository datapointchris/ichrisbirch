"""The chat tables stay gone, and the schema shell that outlives them stays empty.

`d3e4f5a6b7c8` drops `chat.chats`, `chat.messages` and the schema. The schema
comes back on the next `icbops dev start` or `testing start`, because
`POSTGRES_DB_SCHEMAS` still lists `chat` and `create_schemas` runs ahead of
alembic on every init. That entry is required — the baseline migration creates
`chat.chats` inside the schema, so a replay from zero fails without it.

What matters is the tables and their rows, and those do not come back:
`create_schemas` issues `CREATE SCHEMA` and nothing else. These assert that,
so a future change that reintroduces either table fails here rather than in
production.
"""

import sqlalchemy as sa

DROPPED_TABLES = ('chats', 'messages')


def _tables_in_chat_schema(conn) -> list[str]:
    rows = conn.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'chat' ORDER BY table_name"))
    return [r[0] for r in rows]


def test_the_chat_schema_holds_no_tables(factory_session):
    """Present or absent, the schema is empty — the drop removed its contents."""
    assert _tables_in_chat_schema(factory_session.connection()) == []


def test_neither_dropped_table_exists_under_any_schema(factory_session):
    """`chats` and `messages` are unqualified names, so check the whole database.

    A reintroduction under `public` would leave the chat-schema check green
    while putting the tables back.
    """
    conn = factory_session.connection()
    rows = conn.execute(
        sa.text(
            'SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = ANY(:names) AND table_schema NOT LIKE :pg'
        ),
        {'names': list(DROPPED_TABLES), 'pg': 'pg_%'},
    )
    found = [f'{schema}.{table}' for schema, table in rows]
    assert found == [], f'a dropped chat table is back: {found}'
