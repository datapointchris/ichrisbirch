import re

import structlog
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.database.base import Base
from ichrisbirch.models.record_change import RECORDED

CREDENTIAL = re.compile(r'(^|_)(password|secret|token|api_key)$')
AUDIT_TRIGGERS = text("""
    SELECT CASE WHEN n.nspname = 'public' THEN c.relname ELSE n.nspname || '.' || c.relname END, t.tgargs
    FROM pg_trigger AS t
    JOIN pg_class AS c ON c.oid = t.tgrelid
    JOIN pg_namespace AS n ON n.oid = c.relnamespace
    WHERE t.tgname = 'icb_audit_trail'
""")


def test_a_job_write_is_audited_under_its_name_and_never_copies_a_password(txn_api):
    _, session = txn_api
    with structlog.contextvars.bound_contextvars(job_name='make_report', job_run_id='run-1'):
        job_session = Session(bind=session.connection(), join_transaction_mode='create_savepoint')
        user = models.User(name='audited', email='audited@example.com', password='hashed-secret')
        job_session.add(user)
        job_session.flush()
        user_id = str(user.id)
        job_session.delete(user)
        job_session.flush()

    entries = job_session.scalars(
        select(models.RecordChange)
        .where(models.RecordChange.table_name == 'users', models.RecordChange.record_id == user_id)
        .order_by(models.RecordChange.id)
    ).all()
    assert [entry.operation for entry in entries] == ['insert', 'delete']
    assert {(entry.actor, entry.job_run_id) for entry in entries} == {('scheduler/make_report', 'run-1')}
    assert entries[0].changes['email'] == {'new': 'audited@example.com'}
    assert entries[1].changes['email'] == {'old': 'audited@example.com'}
    assert not any('password' in entry.changes for entry in entries)


def test_every_table_is_audited_but_what_opts_out(txn_api):
    """A table's trigger comes from its migration, and its opt-outs from the model, so both must agree.

    A missing table needs `CREATE TRIGGER icb_audit_trail AFTER INSERT OR UPDATE OR DELETE ON <table>
    FOR EACH ROW EXECUTE FUNCTION icb_audit_trail_record('<opted-out column>', ...)` in its migration.
    """
    _, session = txn_api
    triggers = {name: sorted(arg.decode() for arg in bytes(args).split(b'\x00') if arg) for name, args in session.execute(AUDIT_TRIGGERS)}
    audited = [table for table in Base.metadata.sorted_tables if table.info.get(RECORDED, True)]
    expected = {table.fullname: sorted(column.name for column in table.columns if not column.info.get(RECORDED, True)) for table in audited}
    assert triggers == expected

    copied = [
        f'{table.fullname}.{column.name}'
        for table in audited
        for column in table.columns
        if CREDENTIAL.search(column.name) and column.info.get(RECORDED, True)
    ]
    assert copied == [], 'a credential column copied into the audit trail; opt it out'
