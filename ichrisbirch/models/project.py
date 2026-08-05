from __future__ import annotations

from datetime import datetime
from uuid import UUID
from uuid import uuid7

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base

PROJECT_KINDS = ['build', 'chore', 'life']


class ProjectKind(Base):
    """Lookup table for what sort of work a project is, replacing a PostgreSQL ENUM type."""

    __tablename__ = 'project_kinds'
    name: Mapped[str] = mapped_column(Text, primary_key=True)


class Project(Base):
    """An ongoing initiative holding an ordered list of work items.

    `kind` separates making something new from the work that merely has to
    happen, so a consumer asking "what should I build next" is not handed the
    next errand. It defaults to `build` rather than being required: nearly every
    project is one, and a wrong kind is one `PATCH` away, whereas a required
    field breaks every existing caller of the create endpoint.
    """

    __tablename__ = 'projects'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(Text, ForeignKey('project_kinds.name'), nullable=False, server_default='build')
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    memberships: Mapped[list[ProjectItemMembership]] = relationship(
        'ProjectItemMembership', back_populates='project', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'Project(id={self.id!r}, name={self.name!r}, position={self.position!r})'


class ProjectItem(Base):
    __tablename__ = 'project_items'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Registry name from ~/dev/repos.json. Nullable: most items are not repo work.
    repo: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    item: Mapped[ProjectItem] = relationship('ProjectItem', back_populates='tasks')

    __table_args__ = (
        Index('idx_pit_item', 'item_id'),
        Index('idx_pit_position', 'item_id', 'position'),
    )

    def __repr__(self):
        return f'ProjectItemTask(id={self.id!r}, title={self.title!r}, completed={self.completed!r})'
