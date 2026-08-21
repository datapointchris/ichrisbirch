from __future__ import annotations

from datetime import datetime
from uuid import UUID
from uuid import uuid7

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import Uuid
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

PROJECT_KINDS = ['build', 'chore', 'life']
# 'completed' rather than 'done' so one word covers the concept on a project and
# on its items, which store a `completed` boolean. `complete` is the verb on
# both, and it wrote a value called `done` until 2026-08-12.
PROJECT_STATUSES = ['active', 'completed', 'dropped']
TERMINAL_PROJECT_STATUSES = ['completed', 'dropped']

# An item's status is derived from its two booleans rather than stored, so this
# is not a lookup table and there is no FK to it. The precedence is archived over
# completed, which is what the item counts and every client already render.
#
# Deliberately not the same vocabulary as PROJECT_STATUSES. A project is a finite
# effort, so `active` says it is still running; an item is a unit of work, so
# `open` says nobody has done it. They share `completed` because that is the same
# event on both.
ITEM_STATUSES = ['open', 'completed', 'archived']


class ProjectKind(Base):
    """Lookup table for what sort of work a project is, replacing a PostgreSQL ENUM type."""

    __tablename__ = 'project_kinds'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class ProjectStatus(Base):
    """Lookup table for where a project is in its lifecycle, replacing a PostgreSQL ENUM type."""

    __tablename__ = 'project_statuses'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Project(Base):
    """An ongoing initiative holding an ordered list of work items.

    `kind` separates making something new from the work that merely has to
    happen, so a consumer asking "what should I build next" is not handed the
    next errand. It defaults to `build` rather than being required: nearly every
    project is one, and a wrong kind is one `PATCH` away, whereas a required
    field breaks every existing caller of the create endpoint.

    `status` is a field rather than the `archived` boolean items carry, because
    for a project completion and hiding are the same event: a project is a
    finite effort with a definition of done, so there is nothing to archive
    separately. One terminal state would not be enough — `done` alone forces you
    to lie about anything you merely stopped caring about — so `dropped` exists
    beside it and requires a reason, which is what stops a dropped project
    reading as deferred and being re-proposed.

    Closing a project deliberately does NOT cascade to its items. An item still
    open when the project was dropped WAS still open, and 'shipped 8 of 11,
    dropped with 3 open' is the useful fact; archiving all eleven rewrites what
    happened. Visibility is derived from the project instead.
    """

    __tablename__ = 'projects'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    # Unique among ACTIVE projects only — see uq_projects_name_active below.
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(Text, ForeignKey('project_kinds.name'), nullable=False, server_default='build')
    status: Mapped[str] = mapped_column(Text, ForeignKey('project_statuses.name'), nullable=False, server_default='active')
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the project reached a terminal state. `created_at` orders by when work
    # started, which is the wrong axis for a list of finished things, and
    # `position` stops being meaningful once a project is out of the running.
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    memberships: Mapped[list[ProjectItemMembership]] = relationship(
        'ProjectItemMembership', back_populates='project', cascade='all, delete-orphan'
    )

    __table_args__ = (
        CheckConstraint("status <> 'dropped' OR status_reason IS NOT NULL", name='dropped_requires_reason'),
        # Partial, so a finished project stops owning its name and the next
        # effort by that name can be created. A global UNIQUE would fail the
        # insert before any name-resolution rule was consulted.
        Index('uq_projects_name_active', 'name', unique=True, postgresql_where=text("status = 'active'")),
    )

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_PROJECT_STATUSES

    def __repr__(self):
        return f'Project(id={self.id!r}, name={self.name!r}, status={self.status!r}, position={self.position!r})'


class ProjectItem(Base):
    """A unit of work inside one or more projects.

    Two identifiers, because a key and a handle want different things. `id` is
    the key: UUIDv7, generated by whichever client creates the item, so todoui
    can create offline and push without a round trip to claim an id. `number` is
    the handle: server-assigned, short enough to retype, and the only one of the
    two that should ever be printed for a person to read.
    """

    __tablename__ = 'project_items'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    number: Mapped[int] = mapped_column(BigInteger, Identity(always=False), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Repo registry name. Nullable: most items are not repo work.
    repo: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # When the item was finished. `updated_at` is bumped by complete, edit,
    # reopen, archive and unarchive alike, so it cannot answer "what did I finish
    # this week" — it says when the row last moved, not what happened to it.
    # Null means the time is unknown: either the item was never finished, or it
    # was finished by a write that recorded none. Inferring one from `updated_at`
    # would manufacture it, so every reader handles the null instead.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    memberships: Mapped[list[ProjectItemMembership]] = relationship(
        'ProjectItemMembership', back_populates='item', cascade='all, delete-orphan'
    )
    # Read path only. Writes go through ProjectItemMembership, which carries the
    # item's position within each project — a writable secondary would drop it.
    projects: Mapped[list[Project]] = relationship(
        'Project',
        secondary='project_item_memberships',
        viewonly=True,
        order_by='Project.position',
    )
    dependencies: Mapped[list[ProjectItemDependency]] = relationship(
        'ProjectItemDependency',
        foreign_keys='ProjectItemDependency.item_id',
        back_populates='item',
        cascade='all, delete-orphan',
    )
    dependents: Mapped[list[ProjectItemDependency]] = relationship(
        'ProjectItemDependency',
        foreign_keys='ProjectItemDependency.depends_on_id',
        back_populates='depends_on',
        cascade='all, delete-orphan',
    )
    tasks: Mapped[list[ProjectItemTask]] = relationship(
        'ProjectItemTask', back_populates='item', cascade='all, delete-orphan', order_by='ProjectItemTask.position'
    )

    __table_args__ = (Index('idx_pi_active', 'archived', postgresql_where=(archived == False)),)  # noqa: E712

    @property
    def dependency_ids(self) -> list[UUID]:
        """Flatten the dependency edges to the ids consumers actually want.

        Exists so the read schemas can pick this up through `from_attributes`
        instead of every endpoint hand-building the list. Eager-load
        `dependencies` wherever this is serialized in bulk or it lazy-loads
        once per item.
        """
        return [dependency.depends_on_id for dependency in self.dependencies]

    def __repr__(self):
        return f'ProjectItem(id={self.id!r}, title={self.title!r}, completed={self.completed!r})'


class ProjectItemMembership(Base):
    __tablename__ = 'project_item_memberships'
    item_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped[ProjectItem] = relationship('ProjectItem', back_populates='memberships')
    project: Mapped[Project] = relationship('Project', back_populates='memberships')

    __table_args__ = (
        Index('idx_pim_project', 'project_id'),
        Index('idx_pim_item', 'item_id'),
        Index('idx_pim_position', 'project_id', 'position'),
    )

    def __repr__(self):
        return f'ProjectItemMembership(item_id={self.item_id!r}, project_id={self.project_id!r}, position={self.position!r})'


class ProjectItemDependency(Base):
    __tablename__ = 'project_item_dependencies'
    item_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)
    depends_on_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)

    item: Mapped[ProjectItem] = relationship('ProjectItem', foreign_keys=[item_id], back_populates='dependencies')
    depends_on: Mapped[ProjectItem] = relationship('ProjectItem', foreign_keys=[depends_on_id], back_populates='dependents')

    __table_args__ = (
        CheckConstraint('item_id != depends_on_id', name='no_self_dependency'),
        UniqueConstraint('item_id', 'depends_on_id'),
        Index('idx_pid_item', 'item_id'),
        Index('idx_pid_depends', 'depends_on_id'),
    )

    def __repr__(self):
        return f'ProjectItemDependency(item_id={self.item_id!r}, depends_on_id={self.depends_on_id!r})'


class ProjectItemTask(Base):
    __tablename__ = 'project_item_tasks'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    item_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('project_items.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Same reason as the item's, and null under the same two conditions.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    item: Mapped[ProjectItem] = relationship('ProjectItem', back_populates='tasks')

    __table_args__ = (
        Index('idx_pit_item', 'item_id'),
        Index('idx_pit_position', 'item_id', 'position'),
    )

    def __repr__(self):
        return f'ProjectItemTask(id={self.id!r}, title={self.title!r}, completed={self.completed!r})'
