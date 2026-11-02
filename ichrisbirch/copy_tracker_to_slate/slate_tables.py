"""Each slate table the copy writes, and the projection of icb's dumped rows it must equal.

`source` is a SELECT over the `dumped_` tables yielding `columns`. The copy inserts it, and the proof
compares it with `target`, the same columns read back from slate's table. `carries` counts the dumped
rows the source must carry one for one, so a join or a filter cannot drop a row unnoticed.

That proof shares `source` with the insert, so it cannot see a column the source puts in the wrong
place. A second proof reads each column slate keeps from its `counterpart` straight from both tables,
matched by name, and leaves only the `reshaped` columns to the first.

`columns` lists every column of slate's table, and the copy refuses a slate whose catalog says
otherwise. A column icb has no source for is written as its empty value, so the proof reads it too.
Tables are listed in the order their foreign keys need.
"""

from __future__ import annotations

import dataclasses as dc


@dc.dataclass(frozen=True)
class SlateTable:
    name: str
    columns: tuple[str, ...]
    source: str
    carries: str
    # Narrows the target read to the copied rows, where the table already holds slate's own.
    target_filter: str = ''
    # The dumped icb table whose columns slate keeps by name, and the rows of it the table carries.
    counterpart: str | None = None
    counterpart_filter: str = ''
    # slate's name for a column icb named otherwise.
    renamed: dict[str, str] = dc.field(default_factory=dict)
    # Columns the source computes rather than keeps, which only the source proof can read.
    reshaped: frozenset[str] = frozenset()

    def kept_by_name(self, counterpart_columns: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
        """Each (slate column, icb column) pair the table keeps from its counterpart as it was."""
        return tuple(
            (column, self.renamed.get(column, column))
            for column in self.columns
            if column not in self.reshaped and self.renamed.get(column, column) in counterpart_columns
        )

    @property
    def column_list(self) -> str:
        return ', '.join(self.columns)

    @property
    def projection(self) -> str:
        """The source as a FROM item whose columns carry slate's names."""
        return f'({self.source}) AS projected ({self.column_list})'

    @property
    def insert(self) -> str:
        # OVERRIDING SYSTEM VALUE writes an id an identity column declared ALWAYS would refuse.
        return f'INSERT INTO {self.name} ({self.column_list}) OVERRIDING SYSTEM VALUE {self.source}'

    @property
    def target(self) -> str:
        return f'SELECT {self.column_list} FROM {self.name} {self.target_filter}'


# Every initiative by position first, then every issue by rank, ties broken by created_ts and then
# number, renumbered 1 to N. icb holds no ideas, which would follow by number.
RECORDS = SlateTable(
    'records',
    ('number', 'kind', 'rank'),
    source="""
        SELECT number, kind, row_number() OVER (ORDER BY seeding_group, seeding_key, created_ts, number)::double precision AS rank
        FROM (
            SELECT number, 'initiative' AS kind, 0 AS seeding_group, position::double precision AS seeding_key, created_ts
            FROM dumped_initiatives
            UNION ALL
            SELECT number, 'issue', 1, rank, created_ts FROM dumped_issues
        ) AS placed
    """,
    carries='SELECT (SELECT count(*) FROM dumped_initiatives) + (SELECT count(*) FROM dumped_issues)',
)

INITIATIVES = SlateTable(
    'initiatives',
    (
        'id',
        'number',
        'record_kind',
        'name',
        'description',
        'status',
        'status_reason',
        'priority',
        'autofix',
        'created_ts',
        'closed_ts',
        'idea_id',
    ),
    source="""
        SELECT id, number, 'initiative', name, description, status, status_reason, priority, autofix, created_ts, closed_ts, NULL::uuid
        FROM dumped_initiatives
    """,
    carries='SELECT count(*) FROM dumped_initiatives',
    counterpart='initiatives',
)

# slate has no in_progress: a claim says who works an issue, and the issue stays open.
ISSUES = SlateTable(
    'issues',
    (
        'id',
        'number',
        'record_kind',
        'title',
        'description',
        'acceptance',
        'repo',
        'paths',
        'type',
        'status',
        'status_reason',
        'priority',
        'deferred_until_date',
        'autofix',
        'initiative_id',
        'parent_id',
        'discovered_from_id',
        'duplicate_of_id',
        'created_ts',
        'updated_ts',
        'closed_ts',
        'closed_by',
    ),
    source="""
        SELECT id, number, 'issue', title, description, acceptance, repo, '{}'::text[], type,
            CASE WHEN status = 'in_progress' THEN 'open' ELSE status END,
            status_reason, priority, deferred_until_date, autofix, initiative_id, parent_id, discovered_from_id, duplicate_of_id,
            created_ts, updated_ts, closed_ts, closed_by
        FROM dumped_issues
    """,
    carries='SELECT count(*) FROM dumped_issues',
    counterpart='issues',
    reshaped=frozenset({'status'}),
)

ISSUE_DEPENDENCIES = SlateTable(
    'issue_dependencies',
    ('issue_id', 'depends_on_id'),
    source='SELECT issue_id, depends_on_id FROM dumped_issue_dependencies',
    carries='SELECT count(*) FROM dumped_issue_dependencies',
    counterpart='issue_dependencies',
)

ISSUE_LABELS = SlateTable(
    'issue_labels',
    ('id', 'slug', 'group_slug', 'description'),
    source='SELECT id, slug, group_slug, description FROM dumped_issue_labels',
    carries='SELECT count(*) FROM dumped_issue_labels',
    counterpart='issue_labels',
)

ISSUE_LABEL_ASSIGNMENTS = SlateTable(
    'issue_label_assignments',
    ('issue_id', 'label_id'),
    source='SELECT issue_id, label_id FROM dumped_issue_label_assignments',
    carries='SELECT count(*) FROM dumped_issue_label_assignments',
    counterpart='issue_label_assignments',
)

# slate numbers comments 1 to N in the order they were written. icb's UUID stays only as the
# record_id of the comment's own history rows.
COMMENTS = SlateTable(
    'comments',
    ('id', 'record_number', 'document_id', 'version', 'line', 'body', 'written_by', 'session_id', 'worklog_id', 'written_ts'),
    source="""
        SELECT row_number() OVER (ORDER BY comment.created_ts, comment.id), issue.number, NULL::bigint, NULL::integer, NULL::integer,
            comment.body, comment.author, NULL::text, NULL::bigint, comment.created_ts
        FROM dumped_issue_comments AS comment
        JOIN dumped_issues AS issue ON issue.id = comment.issue_id
    """,
    carries='SELECT count(*) FROM dumped_issue_comments',
    counterpart='issue_comments',
    renamed={'written_by': 'author', 'written_ts': 'created_ts'},
    reshaped=frozenset({'id'}),
)

# icb keeps only the claim each issue holds now, so each becomes one unended claim. A claim whose lease
# has run out stays unended with its past expiry, which slate reads as expired. icb never stored when a
# claim began, so it is the moment the audit trail shows the current holder taking it, and failing
# that the earlier of the issue's last update and the expiry.
CLAIMS = SlateTable(
    'claims',
    ('id', 'record_number', 'holder', 'session', 'host', 'directory', 'started_ts', 'expires_ts', 'ended_ts', 'ending', 'ended_by'),
    source="""
        SELECT row_number() OVER (ORDER BY started_ts, record_number), record_number, holder, NULL::text, NULL::text, NULL::text,
            started_ts, expires_ts, NULL::timestamptz, NULL::text, NULL::text
        FROM (
            SELECT issue.number AS record_number, issue.claimed_by AS holder, issue.claim_expires_ts AS expires_ts,
                coalesce(
                    (
                        SELECT max(change.changed_at) FROM dumped_icb_audit_trail AS change
                        WHERE change.table_name = 'issues' AND change.record_id = issue.id::text
                            AND change.changes -> 'claimed_by' ->> 'new' = issue.claimed_by
                    ),
                    least(issue.updated_ts, issue.claim_expires_ts)
                ) AS started_ts
            FROM dumped_issues AS issue
            WHERE issue.claimed_by IS NOT NULL
        ) AS held
    """,
    carries='SELECT count(*) FROM dumped_issues WHERE claimed_by IS NOT NULL',
    counterpart='issues',
    counterpart_filter='WHERE claimed_by IS NOT NULL',
    renamed={'record_number': 'number', 'holder': 'claimed_by', 'expires_ts': 'claim_expires_ts'},
    reshaped=frozenset({'id', 'started_ts'}),
)

# Every row keeps icb's table name, record id, actor and changes as written, in icb's order, under ids
# that follow the rows slate's own history already holds.
AUDIT_TRAIL = SlateTable(
    'audit_trail',
    ('id', 'changed_ts', 'table_name', 'record_id', 'operation', 'changes', 'actor', 'request_id', 'job_run_id'),
    source="""
        SELECT %(audit_baseline)s::bigint + row_number() OVER (ORDER BY changed_at, id), changed_at, table_name, record_id,
            operation, changes, actor, request_id, job_run_id
        FROM dumped_icb_audit_trail
    """,
    carries='SELECT count(*) FROM dumped_icb_audit_trail',
    target_filter='WHERE id > %(audit_baseline)s::bigint',
    counterpart='icb_audit_trail',
    renamed={'changed_ts': 'changed_at'},
    reshaped=frozenset({'id'}),
)

SLATE_TABLES = (RECORDS, INITIATIVES, ISSUES, ISSUE_DEPENDENCIES, ISSUE_LABELS, ISSUE_LABEL_ASSIGNMENTS, COMMENTS, CLAIMS, AUDIT_TRAIL)

# Each table the copy writes carries slate's audit trigger. The copy's own inserts would otherwise
# write a second history beside the one it carries.
AUDITED = tuple(table.name for table in SLATE_TABLES if table is not AUDIT_TRAIL)

# Each identity the copy writes ids into, and the icb sequence those ids came from where icb's are kept.
# A kept id restarts after icb's sequence, because a deleted label's id lives on in its history rows.
IDENTITY_COLUMNS = (('issue_labels', 'issue_labels_id_seq'), ('comments', None), ('claims', None), ('audit_trail', None))

# (table written, column, the lookup table every value of that column must be a row of)
VOCABULARY = (
    (RECORDS, 'kind', 'record_kinds'),
    (INITIATIVES, 'status', 'initiative_statuses'),
    (ISSUES, 'type', 'issue_types'),
    (ISSUES, 'status', 'issue_statuses'),
)
