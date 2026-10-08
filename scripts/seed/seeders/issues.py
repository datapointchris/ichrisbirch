"""Seed issues with initiatives, labels, every edge kind and every claim state.

Each state the ready queue distinguishes is present at least once, so a seeded
dev stack shows every badge and every reason an issue is or is not ready: a
live claim, an expired one, a future deferral, a blocker, a parent waiting on
its children, a triage issue and a decision.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.issue import Initiative
from ichrisbirch.models.issue import Issue
from ichrisbirch.models.issue import IssueComment
from ichrisbirch.models.issue import IssueDependency
from ichrisbirch.models.issue import IssueLabel
from ichrisbirch.models.issue import IssueLabelAssignment
from scripts.seed.base import SeedResult

# (name, description, status, status_reason, priority)
INITIATIVE_DATA = [
    ('Issue tracker', 'Track software work apart from personal projects', 'active', None, 2),
    ('Shared toolchain rollout', 'Every repo on one generated lint and test toolchain', 'active', None, 3),
    ('Docs site refresh', 'One index per repo, every page reachable from it', 'active', None, 0),
    ('Monorepo experiment', 'Fold the CLIs into one module', 'dropped', 'Release cadence differs per tool', 0),
    ('Secrets on SOPS', 'Move every secret to SOPS and age', 'completed', None, 0),
]

# (slug, group_slug, description)
LABEL_DATA = [
    ('area-api', 'area', 'FastAPI endpoints and services'),
    ('area-cli', 'area', 'The Go CLI'),
    ('area-vue', 'area', 'The Vue SPA'),
    ('area-ops', 'area', 'Deploy, routing and containers'),
    ('size-small', 'size', 'Under an hour'),
    ('size-large', 'size', 'More than one session'),
    ('tool-friction', None, 'Filed by a hook from a session that hit friction'),
    ('needs-design', None, 'The shape is not settled yet'),
]

REPOS = ['ichrisbirch', 'dotfiles', 'todoui', None]

# (title, type, status, priority, labels)
ISSUE_DATA = [
    ('Ready queue skips decisions', 'feature', 'open', 2, ['area-api']),
    ('Claim expiry returns issue to the queue', 'feature', 'open', 0, ['area-api', 'size-small']),
    ('icb issues next prints the claimed issue', 'feature', 'open', 3, ['area-cli']),
    ('Issue list filters by label', 'feature', 'open', 0, ['area-vue']),
    ('Rank renumbers when the gap is spent', 'task', 'open', 4, ['area-api', 'size-small']),
    ('Routing file misses the issues paths', 'bug', 'open', 1, ['area-ops']),
    ('Pick the claim default length', 'decision', 'open', 2, ['needs-design']),
    ('Hook filed: link check ran twice', 'chore', 'triage', 0, ['tool-friction']),
    ('Hook filed: pytest output not read', 'chore', 'triage', 0, ['tool-friction']),
    ('Port overview to the issues section', 'task', 'open', 0, ['area-cli', 'size-large']),
    ('Initiative board page', 'feature', 'open', 3, ['area-vue', 'size-large']),
    ('Comment thread on issue detail', 'feature', 'open', 0, ['area-vue']),
    ('Seed every claim state', 'chore', 'completed', 0, ['area-api']),
    ('Bare number resolves across both tables', 'bug', 'completed', 2, ['area-api']),
    ('Hash ids for issues', 'feature', 'canceled', 0, ['needs-design']),
    ('Second ready queue endpoint', 'feature', 'canceled', 0, []),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM issue_comments'))
    session.execute(sqlalchemy.text('DELETE FROM issue_label_assignments'))
    session.execute(sqlalchemy.text('DELETE FROM issue_dependencies'))
    session.execute(sqlalchemy.text('DELETE FROM issues'))
    session.execute(sqlalchemy.text('DELETE FROM issue_labels'))
    session.execute(sqlalchemy.text('DELETE FROM initiatives'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    now = datetime.now(UTC)

    initiatives = []
    for rep in range(scale):
        for position, (name, description, initiative_status, reason, priority) in enumerate(INITIATIVE_DATA):
            initiatives.append(
                Initiative(
                    name=name if scale == 1 else f'{name} #{rep + 1}',
                    description=description,
                    status=initiative_status,
                    status_reason=reason,
                    priority=priority,
                    position=position,
                    closed_ts=None if initiative_status == 'active' else now - timedelta(days=20),
                )
            )
    session.add_all(initiatives)

    labels = {slug: IssueLabel(slug=slug, group_slug=group, description=description) for slug, group, description in LABEL_DATA}
    session.add_all(labels.values())
    session.flush()

    active_initiatives = [initiative for initiative in initiatives if initiative.status == 'active']
    issues: list[Issue] = []
    for idx in range(len(ISSUE_DATA) * scale):
        title, issue_type, issue_status, priority, label_slugs = ISSUE_DATA[idx % len(ISSUE_DATA)]
        if idx >= len(ISSUE_DATA):
            title = f'{title} #{idx // len(ISSUE_DATA) + 1}'
        closed = issue_status in ('completed', 'canceled')
        issue = Issue(
            title=title,
            description=f'Seeded issue {idx + 1}. What the repo does not already say goes here.',
            acceptance='The behavior is covered by a test that fails without the change.' if idx % 2 == 0 else None,
            repo=REPOS[idx % len(REPOS)],
            type=issue_type,
            status=issue_status,
            status_reason='Superseded by a server-side queue' if issue_status == 'canceled' else None,
            priority=priority,
            rank=float(idx + 1),
            initiative_id=active_initiatives[idx % len(active_initiatives)].id if idx % 3 != 2 else None,
            created_ts=now - timedelta(days=60 - idx),
            updated_ts=now - timedelta(days=(60 - idx) // 2),
            closed_ts=now - timedelta(days=idx % 30) if closed else None,
        )
        issue.label_assignments = [IssueLabelAssignment(label_id=labels[slug].id) for slug in label_slugs]
        issues.append(issue)
    session.add_all(issues)
    session.flush()

    by_title = {issue.title: issue for issue in issues}

    # A live claim, and one that expired: the expired one is back in the queue.
    live = by_title['icb issues next prints the claimed issue']
    live.status, live.claimed_by, live.claim_expires_ts = 'in_progress', 'seed-session-live', now + timedelta(hours=3)
    stale = by_title['Issue list filters by label']
    stale.status, stale.claimed_by, stale.claim_expires_ts = 'in_progress', 'seed-session-gone', now - timedelta(hours=1)

    # Deferred and nothing else, so the deferral alone keeps it out of the queue.
    by_title['Comment thread on issue detail'].deferred_until_date = (now + timedelta(days=14)).date()

    # A parent waiting on its children, one of them already completed.
    parent = by_title['Initiative board page']
    for child_title in ('Comment thread on issue detail', 'Seed every claim state'):
        by_title[child_title].parent_id = parent.id

    # One blocker gating two issues, and one issue waiting on two. The
    # low-priority rank fix gates the urgent routing bug, so it inherits urgent
    # in the ready queue.
    edges = [
        ('Routing file misses the issues paths', 'Rank renumbers when the gap is spent'),
        ('Claim expiry returns issue to the queue', 'Ready queue skips decisions'),
        ('Port overview to the issues section', 'Ready queue skips decisions'),
        ('Port overview to the issues section', 'icb issues next prints the claimed issue'),
    ]
    for waiter, blocker in edges:
        session.add(IssueDependency(issue_id=by_title[waiter].id, depends_on_id=by_title[blocker].id))

    by_title['Hook filed: pytest output not read'].discovered_from_id = by_title['Ready queue skips decisions'].id
    duplicate = by_title['Second ready queue endpoint']
    duplicate.status_reason = None
    duplicate.duplicate_of_id = by_title['Ready queue skips decisions'].id

    comments = [
        IssueComment(issue_id=live.id, body='Claimed. Starting with the CLI output shape.', author='seed-session-live'),
        IssueComment(issue_id=live.id, body='JSON shape settled; table output next.', author='seed-session-live'),
        IssueComment(issue_id=by_title['Bare number resolves across both tables'].id, body='Shipped with the shared sequence.'),
    ]
    session.add_all(comments)
    session.flush()

    open_count = sum(1 for issue in issues if issue.status not in ('completed', 'canceled'))
    return SeedResult(
        model='Issue',
        count=len(initiatives) + len(labels) + len(issues) + len(comments),
        details=(
            f'{len(initiatives)} initiatives, {len(labels)} labels, {len(issues)} issues ({open_count} open), '
            f'{len(edges)} deps, {len(comments)} comments'
        ),
    )
