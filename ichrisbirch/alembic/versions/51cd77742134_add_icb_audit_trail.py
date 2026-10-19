"""add icb audit trail

Revision ID: 51cd77742134
Revises: 532aec322f58
Create Date: 2026-10-19 00:03:42.057025

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '51cd77742134'
down_revision = '532aec322f58'
branch_labels = None
depends_on = None

# A new table takes its trigger in its own migration:
#   CREATE TRIGGER icb_audit_trail AFTER INSERT OR UPDATE OR DELETE ON <table>
#   FOR EACH ROW EXECUTE FUNCTION icb_audit_trail_record('<secret column>', ...)
NOT_AUDITED = {
    ('public', 'alembic_version'),
    ('public', 'apscheduler_jobs'),
    ('public', 'icb_audit_trail'),
    ('admin', 'scheduler_job_runs'),
}
SECRET_COLUMNS = {('public', 'users'): ('password',)}

RECORD_FUNCTION = """
CREATE FUNCTION icb_audit_trail_record() RETURNS trigger LANGUAGE plpgsql AS $$
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

    old_row := old_row - coalesce(TG_ARGV, '{}'::text[]);
    new_row := new_row - coalesce(TG_ARGV, '{}'::text[]);
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

    INSERT INTO icb_audit_trail (table_name, record_id, operation, changes, actor, request_id, job_run_id)
    VALUES (
        CASE WHEN TG_TABLE_SCHEMA = 'public' THEN TG_TABLE_NAME ELSE TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME END,
        coalesce(primary_key_text, ''),
        lower(TG_OP),
        written,
        nullif(current_setting('icb.actor', true), ''),
        nullif(current_setting('icb.request_id', true), ''),
        nullif(current_setting('icb.job_run_id', true), '')
    );
    RETURN NULL;
END;
$$
"""


def owned_tables() -> list[tuple[str, str]]:
    query = sa.text(
        "SELECT schemaname, tablename FROM pg_tables WHERE tableowner = current_user AND schemaname NOT IN ('pg_catalog', 'information_schema')"
    )
    return [(schema, table) for schema, table in op.get_bind().execute(query)]


def upgrade() -> None:
    op.create_table(
        'icb_audit_trail',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('table_name', sa.Text(), nullable=False),
        sa.Column('record_id', sa.Text(), nullable=False),
        sa.Column('operation', sa.Text(), nullable=False),
        sa.Column('changes', postgresql.JSONB(), nullable=False),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('request_id', sa.Text(), nullable=True),
        sa.Column('job_run_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_icb_audit_trail')),
        sa.CheckConstraint(
            "operation IN ('insert', 'update', 'delete')",
            name=op.f('ck_icb_audit_trail_operation_is_a_write'),
        ),
    )
    op.create_index('idx_icb_audit_trail_record', 'icb_audit_trail', ['table_name', 'record_id', 'changed_at'])
    op.create_index(op.f('ix_icb_audit_trail_changed_at'), 'icb_audit_trail', ['changed_at'])
    op.create_index(op.f('ix_icb_audit_trail_actor'), 'icb_audit_trail', ['actor'])
    op.execute(RECORD_FUNCTION)
    for schema, table in owned_tables():
        if (schema, table) in NOT_AUDITED:
            continue
        secrets = ', '.join(f"'{column}'" for column in SECRET_COLUMNS.get((schema, table), ()))
        op.execute(
            f'CREATE TRIGGER icb_audit_trail AFTER INSERT OR UPDATE OR DELETE ON "{schema}"."{table}" '
            f'FOR EACH ROW EXECUTE FUNCTION icb_audit_trail_record({secrets})'
        )


def downgrade() -> None:
    for schema, table in owned_tables():
        op.execute(f'DROP TRIGGER IF EXISTS icb_audit_trail ON "{schema}"."{table}"')
    op.execute('DROP FUNCTION icb_audit_trail_record()')
    op.drop_table('icb_audit_trail')
