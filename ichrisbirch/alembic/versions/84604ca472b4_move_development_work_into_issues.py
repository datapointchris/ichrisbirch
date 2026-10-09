"""Move development work out of projects and into issues

When this runs, a `build` project holds development work. Every `build` project
becomes an initiative with the same id. Every item whose projects are all
`build` becomes an issue with the same id and number. A `chore` project stays,
because its kind marks work that has to happen and makes nothing new. An item
that also sits in a project of another kind stays a project item, and loses its
membership in the projects that moved.

Initiative status: completed and dropped carry over, and active and someday
both become active. Priority ranks the active projects by position into
thirds: high (2), medium (3) and low (4). Every other initiative gets none (0).

Issue status: a completed item is completed, even when it was also archived,
because the work was done. An item archived without being completed is
canceled, with a reason. Every other item is open. Notes become the
description, and sub-tasks become a checklist in `acceptance`. Each issue gets
priority 0, so it ranks by its initiative.

An item in several projects joins one initiative: its active project with the
lowest position, else its project with the lowest position. Rank is that
project's place, then the item's position in it, so each issue keeps the place
its project queued it in. The moved issues rank after every issue that already
exists.

A dependency between two moved items is copied. An edge between a moved item
and one that stays cannot cross tables. It becomes a line on the dependent
side naming the other's number.

The move deletes the projects and items it copied, and no downgrade can
restore them. Each left an initiative or an issue behind, so the downgrade
refuses while either table holds a row. With both empty there is nothing to
undo, and the downgrade only moves the revision back.

Revision ID: 84604ca472b4
Revises: d9e0f1a2b3c4
Create Date: 2026-10-08

"""

import sqlalchemy as sa
from alembic import op

revision = '84604ca472b4'
down_revision = 'd9e0f1a2b3c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TEMP TABLE moving_items AS
        SELECT membership.item_id AS id
        FROM project_item_memberships membership
        JOIN projects project ON project.id = membership.project_id
        GROUP BY membership.item_id
        HAVING bool_and(project.kind = 'build')
    """)
    op.execute("""
        CREATE TEMP TABLE primary_memberships AS
        SELECT DISTINCT ON (membership.item_id)
            membership.item_id,
            membership.project_id,
            membership.position AS item_position,
            project.status = 'active' AS project_active,
            project.position AS project_position,
            project.created_at AS project_created_at
        FROM project_item_memberships membership
        JOIN projects project ON project.id = membership.project_id
        JOIN moving_items moving ON moving.id = membership.item_id
        ORDER BY membership.item_id, project.status = 'active' DESC, project.position, project.created_at, project.id
    """)

    op.execute("""
        INSERT INTO initiatives (id, name, description, status, status_reason, priority, position, created_ts, closed_ts)
        SELECT
            project.id,
            project.name,
            project.description,
            CASE WHEN project.status IN ('completed', 'dropped') THEN project.status ELSE 'active' END,
            project.status_reason,
            COALESCE(band.priority, 0),
            project.position,
            project.created_at,
            project.closed_at
        FROM projects project
        LEFT JOIN (
            SELECT id, ntile(3) OVER (ORDER BY position, created_at, id) + 1 AS priority
            FROM projects
            WHERE kind = 'build' AND status = 'active'
        ) band ON band.id = project.id
        WHERE project.kind = 'build'
    """)

    op.execute("""
        INSERT INTO issues (
            id, number, title, description, acceptance, repo, type, status, status_reason,
            priority, rank, initiative_id, created_ts, updated_ts, closed_ts
        )
        SELECT
            item.id,
            item.number,
            item.title,
            item.notes,
            checklist.body,
            item.repo,
            'task',
            CASE WHEN item.completed THEN 'completed' WHEN item.archived THEN 'canceled' ELSE 'open' END,
            CASE WHEN item.archived AND NOT item.completed THEN 'Archived as a project item' END,
            0,
            (SELECT COALESCE(MAX(rank), 0) FROM issues) + row_number() OVER (
                ORDER BY
                    placed.project_active DESC,
                    placed.project_position,
                    placed.project_created_at,
                    placed.project_id,
                    placed.item_position,
                    item.created_at,
                    item.id
            ),
            placed.project_id,
            item.created_at,
            item.updated_at,
            CASE WHEN item.completed THEN item.completed_at END
        FROM project_items item
        JOIN primary_memberships placed ON placed.item_id = item.id
        LEFT JOIN (
            SELECT
                item_id,
                string_agg(
                    CASE WHEN completed THEN '- [x] ' ELSE '- [ ] ' END || title, E'\\n' ORDER BY position, created_at, id
                ) AS body
            FROM project_item_tasks
            GROUP BY item_id
        ) checklist ON checklist.item_id = item.id
    """)

    op.execute("""
        INSERT INTO issue_dependencies (issue_id, depends_on_id)
        SELECT edge.item_id, edge.depends_on_id
        FROM project_item_dependencies edge
        JOIN moving_items dependent ON dependent.id = edge.item_id
        JOIN moving_items dependency ON dependency.id = edge.depends_on_id
    """)

    op.execute("""
        UPDATE issues
        SET description = concat_ws(E'\\n\\n', issues.description, crossing.lines)
        FROM (
            SELECT edge.item_id, string_agg('Depends on project item ' || staying.number || '.', E'\\n' ORDER BY staying.number) AS lines
            FROM project_item_dependencies edge
            JOIN moving_items dependent ON dependent.id = edge.item_id
            JOIN project_items staying ON staying.id = edge.depends_on_id
            WHERE edge.depends_on_id NOT IN (SELECT id FROM moving_items)
            GROUP BY edge.item_id
        ) crossing
        WHERE issues.id = crossing.item_id
    """)
    op.execute("""
        UPDATE project_items
        SET notes = concat_ws(E'\\n\\n', project_items.notes, crossing.lines), updated_at = now()
        FROM (
            SELECT edge.item_id, string_agg('Depends on issue ' || moved.number || '.', E'\\n' ORDER BY moved.number) AS lines
            FROM project_item_dependencies edge
            JOIN moving_items dependency ON dependency.id = edge.depends_on_id
            JOIN project_items moved ON moved.id = edge.depends_on_id
            WHERE edge.item_id NOT IN (SELECT id FROM moving_items)
            GROUP BY edge.item_id
        ) crossing
        WHERE project_items.id = crossing.item_id
    """)

    op.execute('DELETE FROM project_items WHERE id IN (SELECT id FROM moving_items)')
    op.execute("DELETE FROM projects WHERE kind = 'build'")

    op.execute('DROP TABLE primary_memberships')
    op.execute('DROP TABLE moving_items')


def downgrade() -> None:
    holds_rows = op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT FROM issues) OR EXISTS (SELECT FROM initiatives)'))
    if holds_rows:
        raise NotImplementedError(
            'issues or initiatives hold rows, and the move into them dropped secondary memberships, '
            'the archived flag on completed items and sub-task rows; restore from backup'
        )
