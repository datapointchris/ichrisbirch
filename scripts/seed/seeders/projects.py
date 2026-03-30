"""Seed projects with items, memberships, dependencies, and tasks.

Extracted from the former _seed_project_ecosystem() — this was already
the right pattern (explicit, coordinated multi-table insertion).
"""

from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.project import Project
from ichrisbirch.models.project import ProjectItem
from ichrisbirch.models.project import ProjectItemDependency
from ichrisbirch.models.project import ProjectItemMembership
from ichrisbirch.models.project import ProjectItemTask
from scripts.seed.base import SeedResult

PROJECT_DATA = [
    ('Home Renovation', 'Kitchen and bathroom remodel planning'),
    ('Learn Kubernetes', 'Self-study track for container orchestration'),
    ('Career Development', 'Skills growth and networking goals'),
    ('Side Project: Budget CLI', 'Command-line tool for personal finance tracking'),
    ('Fitness Goals 2026', 'Strength training and running milestones'),
    ('Portland Trip Planning', 'Research neighborhoods, flights, and activities'),
]

ITEM_TITLES = [
    'Research options and alternatives',
    'Create detailed project plan',
    'Set up development environment',
    'Write initial documentation',
    'Design system architecture',
    'Implement core functionality',
    'Write tests and validation',
    'Code review and refactoring',
    'Set up deployment pipeline',
    'Deploy to staging environment',
    'Gather user feedback',
    'Fix reported issues',
    'Performance optimization pass',
    'Security audit and hardening',
    'Update project dependencies',
    'Create monitoring dashboards',
    'Write runbook for operations',
    'Plan next milestone',
    'Coordinate with stakeholders',
    'Final review and release',
]

ITEM_NOTES = [
    'Need to compare at least 3 options before deciding',
    'Check if there are any blockers from other teams',
    'Should be done before the end of the month',
    'Low priority but good to have eventually',
    'Discuss approach in next standup',
    'Reference docs are in the shared drive',
    'Blocked until upstream dependency is resolved',
]

TASK_TITLES = [
    'Review requirements',
    'Draft implementation',
    'Write unit tests',
    'Update documentation',
    'Get approval',
]

# (completed, archived) — weighted toward active
STATE_CYCLE = [
    (False, False),
    (False, False),
    (False, False),
    (True, False),
    (False, True),
    (True, True),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM project_item_tasks'))
    session.execute(sqlalchemy.text('DELETE FROM project_item_dependencies'))
    session.execute(sqlalchemy.text('DELETE FROM project_item_memberships'))
    session.execute(sqlalchemy.text('DELETE FROM project_items'))
    session.execute(sqlalchemy.text('DELETE FROM projects'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    # Create projects
    projects = []
    for rep in range(scale):
        for i, (name, description) in enumerate(PROJECT_DATA):
            proj_name = name if scale == 1 else f'{name} #{rep + 1}'
            projects.append(Project(name=proj_name, description=description, position=i))
    session.add_all(projects)
    session.flush()

    project_ids = [p.id for p in projects]

    # Create items with explicit state coverage
    items = []
    target_count = len(ITEM_TITLES) * scale
    for idx in range(target_count):
        title = ITEM_TITLES[idx % len(ITEM_TITLES)]
        if scale > 1 and idx >= len(ITEM_TITLES):
            title = f'{title} #{idx // len(ITEM_TITLES) + 1}'
        completed, archived = STATE_CYCLE[idx % len(STATE_CYCLE)]
        notes = ITEM_NOTES[idx % len(ITEM_NOTES)] if idx % 3 != 0 else None
        items.append(ProjectItem(title=title, notes=notes, completed=completed, archived=archived))

    session.add_all(items)
    session.flush()

    # Memberships: distribute round-robin, ~25% get dual membership
    membership_count = 0
    for i, item in enumerate(items):
        primary = project_ids[i % len(project_ids)]
        session.add(ProjectItemMembership(item_id=item.id, project_id=primary, position=i // len(project_ids)))
        membership_count += 1

        if i % 4 == 0 and len(project_ids) > 1:
            secondary = project_ids[(i + 1) % len(project_ids)]
            session.add(ProjectItemMembership(item_id=item.id, project_id=secondary, position=99))
            membership_count += 1
    session.flush()

    # Dependencies: short chains within each project (acyclic by construction)
    dep_count = 0
    items_by_project: dict[object, list[object]] = {}
    for i, item in enumerate(items):
        proj = project_ids[i % len(project_ids)]
        items_by_project.setdefault(proj, []).append(item.id)

    for item_ids_in_proj in items_by_project.values():
        chain_len = min(3, len(item_ids_in_proj))
        for j in range(1, chain_len):
            session.add(
                ProjectItemDependency(
                    item_id=item_ids_in_proj[j],
                    depends_on_id=item_ids_in_proj[j - 1],
                )
            )
            dep_count += 1
    session.flush()

    # Tasks: ~60% of items get 1-3 sub-tasks
    task_count = 0
    for i, item in enumerate(items):
        if i % 5 < 3:
            num_tasks = (i % 3) + 1
            for t in range(num_tasks):
                session.add(
                    ProjectItemTask(
                        item_id=item.id,
                        title=TASK_TITLES[t % len(TASK_TITLES)],
                        completed=(t == 0 and i % 2 == 0),
                        position=t,
                    )
                )
                task_count += 1
    session.flush()

    active = sum(1 for item in items if not item.completed and not item.archived)
    return SeedResult(
        model='Project',
        count=len(projects) + len(items) + task_count,
        details=(
            f'{len(projects)} projects, {len(items)} items ({active} active), '
            f'{membership_count} memberships, {dep_count} deps, {task_count} tasks'
        ),
    )
