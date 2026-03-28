from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base


class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    memberships: Mapped[list['ProjectItemMembership']] = relationship(
        'ProjectItemMembership', back_populates='project', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'Project(id={self.id!r}, name={self.name!r}, position={self.position!r})'


class ProjectItem(Base):
    __tablename__ = 'project_items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default='now()')

    memberships: Mapped[list['ProjectItemMembership']] = relationship(
        'ProjectItemMembership', back_populates='item', cascade='all, delete-orphan'
    )
    dependencies: Mapped[list['ProjectItemDependency']] = relationship(
        'ProjectItemDependency',
        foreign_keys='ProjectItemDependency.item_id',
        back_populates='item',
        cascade='all, delete-orphan',
    )
    dependents: Mapped[list['ProjectItemDependency']] = relationship(
        'ProjectItemDependency',
        foreign_keys='ProjectItemDependency.depends_on_id',
        back_populates='depends_on',
        cascade='all, delete-orphan',
    )

    __table_args__ = (Index('idx_pi_active', 'archived', postgresql_where=(archived == False)),)  # noqa: E712

    def __repr__(self):
        return f'ProjectItem(id={self.id!r}, title={self.title!r}, completed={self.completed!r})'


class ProjectItemMembership(Base):
    __tablename__ = 'project_item_memberships'
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped['ProjectItem'] = relationship('ProjectItem', back_populates='memberships')
    project: Mapped['Project'] = relationship('Project', back_populates='memberships')

    __table_args__ = (
        Index('idx_pim_project', 'project_id'),
        Index('idx_pim_item', 'item_id'),
        Index('idx_pim_position', 'project_id', 'position'),
    )

    def __repr__(self):
        return f'ProjectItemMembership(item_id={self.item_id!r}, project_id={self.project_id!r}, position={self.position!r})'


class ProjectItemDependency(Base):
    __tablename__ = 'project_item_dependencies'
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)
    depends_on_id: Mapped[int] = mapped_column(Integer, ForeignKey('project_items.id', ondelete='CASCADE'), primary_key=True)

    item: Mapped['ProjectItem'] = relationship('ProjectItem', foreign_keys=[item_id], back_populates='dependencies')
    depends_on: Mapped['ProjectItem'] = relationship('ProjectItem', foreign_keys=[depends_on_id], back_populates='dependents')

    __table_args__ = (
        CheckConstraint('item_id != depends_on_id', name='no_self_dependency'),
        UniqueConstraint('item_id', 'depends_on_id'),
        Index('idx_pid_item', 'item_id'),
        Index('idx_pid_depends', 'depends_on_id'),
    )

    def __repr__(self):
        return f'ProjectItemDependency(item_id={self.item_id!r}, depends_on_id={self.depends_on_id!r})'
