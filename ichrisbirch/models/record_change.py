"""Every write to a mapped table leaves a row in `icb_audit_trail`, naming who made it.

The listener reads each flush's inserts, updates and deletes from the unit of work, so a route, a
scheduler job and a script record their writes without calling anything. The caller rides on the
session: the API binds the signed-in user's email or the service client's id where it resolves the
caller, and a scheduler job is named by the `job_name` its wrapper binds into structlog's context.

An update that bypasses the unit of work records itself with `record_update`. The rank
renumbering in `services/fractional_rank.py` records nothing, because it keeps every row's order.

A table opts out with `'info': {'record_changes': False}` in its `__table_args__`, and a column
with the same key in its `info`.
"""

import datetime as dt
from typing import Any

import structlog
from pydantic_core import to_jsonable_python
from sqlalchemy import BigInteger
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import Identity
from sqlalchemy import Index
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.state import InstanceState

from ichrisbirch.database.base import Base

RECORDED = 'record_changes'
ACTOR = 'record_changes_actor'


class RecordChange(Base):
    """One write to one row of any table, and who made it.

    `changes` maps each column the write touched to `{"old": ..., "new": ...}`. An insert carries no
    `old`, a delete no `new`, and an update leaves `old` out where the session never loaded it.
    """

    __tablename__ = 'icb_audit_trail'
    __table_args__ = (
        CheckConstraint("operation IN ('insert', 'update', 'delete')", name='operation_is_a_write'),
        Index('idx_icb_audit_trail_record', 'table_name', 'record_id', 'changed_at'),
        {'info': {RECORDED: False}},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    changed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    table_name: Mapped[str] = mapped_column(Text, nullable=False)
    record_id: Mapped[str] = mapped_column(Text, nullable=False)
    operation: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    actor: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_run_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f'RecordChange({self.operation} {self.table_name}/{self.record_id} by {self.actor!r})'


def bind_actor(session: Session, actor: str) -> None:
    """Name who makes every write `session` flushes from here on."""
    session.info[ACTOR] = actor


def record_update(session: Session, obj: Any, values: dict[str, Any]) -> None:
    """Record `values` written to `obj` by a statement the unit of work never saw.

    Call it before anything refreshes `obj`, which still holds the values the statement replaced.
    """
    state = inspect(obj)
    written = {}
    for key, value in values.items():
        written[key] = {'new': jsonable(value)}
        if key in state.dict:
            written[key]['old'] = jsonable(state.dict[key])
    if row := change_row(obj, 'update', written):
        session.connection().execute(insert(RecordChange), [row | caller_columns(session)])


def caller_columns(session: Session) -> dict[str, str | None]:
    bound = structlog.contextvars.get_contextvars()
    job_name = bound.get('job_name')
    actor = session.info.get(ACTOR) or (f'scheduler/{job_name}' if job_name else None)
    return {'actor': actor, 'request_id': bound.get('request_id'), 'job_run_id': bound.get('job_run_id')}


def recorded_keys(mapper: Mapper, table: Table) -> list[str]:
    if not table.info.get(RECORDED, True):
        return []
    return [attr.key for attr in mapper.column_attrs if attr.columns[0].info.get(RECORDED, True)]


def jsonable(value: Any) -> Any:
    return to_jsonable_python(value, fallback=str)


def written_columns(state: InstanceState, keys: list[str], operation: str) -> dict[str, dict[str, Any]]:
    if operation == 'insert':
        return {key: {'new': jsonable(state.dict[key])} for key in keys if key in state.dict}
    if operation == 'delete':
        return {key: {'old': jsonable(state.dict[key])} for key in keys if key in state.dict}
    changed = {}
    for key in keys:
        history = state.attrs[key].history
        if not history.has_changes():
            continue
        changed[key] = {'new': jsonable(history.added[0] if history.added else None)}
        if history.deleted:
            changed[key]['old'] = jsonable(history.deleted[0])
    return changed


def change_row(obj: Any, operation: str, written: dict[str, dict[str, Any]] | None = None) -> dict[str, Any] | None:
    state = inspect(obj)
    mapper = state.mapper
    table = mapper.persist_selectable
    if not isinstance(table, Table) or not (keys := recorded_keys(mapper, table)):
        return None
    if written is None:
        changes = written_columns(state, keys, operation)
    else:
        changes = {key: change for key, change in written.items() if key in keys}
    if not changes:
        return None
    record_id = ','.join(str(state.dict.get(mapper.get_property_by_column(column).key)) for column in mapper.primary_key)
    return {'table_name': table.fullname, 'record_id': record_id, 'operation': operation, 'changes': changes}


@event.listens_for(Session, 'after_flush')
def record_flushed_changes(session: Session, _flush_context: Any) -> None:
    """Record what this flush wrote. The session still holds the pre-flush history here."""
    written = [(obj, 'insert') for obj in session.new]
    written += [(obj, 'update') for obj in session.dirty if session.is_modified(obj, include_collections=False)]
    written += [(obj, 'delete') for obj in session.deleted]
    rows = [row for obj, operation in written if (row := change_row(obj, operation))]
    if rows:
        caller = caller_columns(session)
        session.connection().execute(insert(RecordChange), [row | caller for row in rows])
