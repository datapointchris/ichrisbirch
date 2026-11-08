"""rename the audit trail to life_audit_trail

Revision ID: bb7c7a9de024
Revises: c6092e8133ed
Create Date: 2026-11-08 15:11:00.370855

The table, its function, the trigger on every audited table, its indexes, its
constraints and its identity sequence all take the app's name. Every name moves
by OID, so the trail keeps every row and each trigger keeps its arguments.

The function's body names the table and the session settings it reads, so it is
replaced rather than renamed, and `record_change.py` sets `life.actor`,
`life.request_id` and `life.job_run_id` to match.

The release that carries this is the one that also moves the deployment to its
new names, and that move stops the serving color before it migrates. So no code
reading the old names runs beside this migration, which a rename otherwise needs.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bb7c7a9de024'
down_revision = 'c6092e8133ed'
branch_labels = None
depends_on = None

# Each object named after the table, with `{t}` where the table's name goes.
INDEXES = ('pk_{t}', 'idx_{t}_record', 'ix_{t}_changed_at', 'ix_{t}_actor')
CONSTRAINTS = ('ck_{t}_operation_is_a_write',)
SEQUENCE = '{t}_id_seq'

RECORD_FUNCTION = """
CREATE OR REPLACE FUNCTION {name}_record() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    old_row jsonb := CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END;
    new_row jsonb := CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END;
    primary_key_text text;
    written jsonb;
BEGIN
    SELECT string_agg(coalesce(new_row, old_row) ->> a.attname, ',' ORDER BY k.position) INTO primary_key_text
    FROM pg_index AS i
    CROSS JOIN LATERAL unnest(i.indkey::int2[]) WITH ORDINALITY AS k(attnum, position)
    JOIN pg_attribute AS a ON a.attrelid = i.indrelid AND a.attnum = k.attnum
    WHERE i.indrelid = TG_RELID AND i.indisprimary;

    old_row := old_row - coalesce(TG_ARGV, '{{}}'::text[]);
    new_row := new_row - coalesce(TG_ARGV, '{{}}'::text[]);
    IF TG_OP = 'INSERT' THEN
        SELECT jsonb_object_agg(n.key, jsonb_build_object('new', n.value)) INTO written FROM jsonb_each(new_row) AS n;
    ELSIF TG_OP = 'DELETE' THEN
        SELECT jsonb_object_agg(o.key, jsonb_build_object('old', o.value)) INTO written FROM jsonb_each(old_row) AS o;
    ELSE
        SELECT jsonb_object_agg(n.key, jsonb_build_object('old', o.value, 'new', n.value)) INTO written
        FROM jsonb_each(new_row) AS n JOIN jsonb_each(old_row) AS o ON o.key = n.key
        WHERE n.value IS DISTINCT FROM o.value;
    END IF;
    IF written IS NULL THEN
        RETURN NULL;
    END IF;

    INSERT INTO {name} (table_name, record_id, operation, changes, actor, request_id, job_run_id)
    VALUES (
        CASE WHEN TG_TABLE_SCHEMA = 'public' THEN TG_TABLE_NAME ELSE TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME END,
        coalesce(primary_key_text, ''),
        lower(TG_OP),
        written,
        nullif(current_setting('{setting}.actor', true), ''),
        nullif(current_setting('{setting}.request_id', true), ''),
        nullif(current_setting('{setting}.job_run_id', true), '')
    );
    RETURN NULL;
END;
$$
"""


def audited_tables(trigger: str) -> list[tuple[str, str]]:
    query = sa.text(
        'SELECT n.nspname, c.relname FROM pg_trigger AS t JOIN pg_class AS c ON c.oid = t.tgrelid '
        'JOIN pg_namespace AS n ON n.oid = c.relnamespace WHERE t.tgname = :trigger AND NOT t.tgisinternal'
    )
    return [(schema, table) for schema, table in op.get_bind().execute(query, {'trigger': trigger})]


def rename(old: str, new: str, setting: str) -> None:
    op.rename_table(old, new)
    for index in INDEXES:
        op.execute(f'ALTER INDEX {index.format(t=old)} RENAME TO {index.format(t=new)}')
    for constraint in CONSTRAINTS:
        op.execute(f'ALTER TABLE {new} RENAME CONSTRAINT {constraint.format(t=old)} TO {constraint.format(t=new)}')
    op.execute(f'ALTER SEQUENCE {SEQUENCE.format(t=old)} RENAME TO {SEQUENCE.format(t=new)}')
    op.execute(f'ALTER FUNCTION {old}_record() RENAME TO {new}_record')
    op.execute(RECORD_FUNCTION.format(name=new, setting=setting))
    for schema, table in audited_tables(old):
        op.execute(f'ALTER TRIGGER {old} ON "{schema}"."{table}" RENAME TO {new}')


def upgrade() -> None:
    rename('icb_audit_trail', 'life_audit_trail', 'life')


def downgrade() -> None:
    rename('life_audit_trail', 'icb_audit_trail', 'icb')
