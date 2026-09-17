"""The chat schema and its tables stay gone.

`d3e4f5a6b7c8` drops `chat.chats`, `chat.messages` and the schema. The baseline
revision creates the schema it writes into, so nothing ahead of alembic creates
`chat` and initialization run again at head does not put it back. These assert
that, so a change that reintroduces the schema or either table fails here
rather than in production.
"""

import sqlalchemy as sa

from ichrisbirch.database.initialization import full_initialization
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

DROPPED_TABLES = ('chats', 'messages')


def _tables_in_chat_schema(conn) -> list[str]:
    rows = conn.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'chat' ORDER BY table_name"))
    return [r[0] for r in rows]


def test_the_chat_schema_holds_no_tables(factory_session):
    assert _tables_in_chat_schema(factory_session.connection()) == []


def test_initialization_at_head_does_not_recreate_the_chat_schema():
    """Every checkout shares the test database, and older initializers recreated `chat`.

    The drop is not CASCADE, so it refuses a `chat` that still holds tables.
    """
    engine = get_db_engine(test_settings)
    with engine.begin() as conn:
        conn.execute(sa.text('DROP SCHEMA IF EXISTS chat'))

    full_initialization(test_settings)

    with engine.connect() as conn:
        assert 'chat' not in sa.inspect(conn).get_schema_names()


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
