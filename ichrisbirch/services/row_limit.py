"""Row capping for the collection reads, with one meaning for zero.

`cli-design.md` § "`--follow`/`-f` defaults to false; `--limit`/`-n` goes on
every list" puts a limit on every list over data that grows outside the binary,
which is every collection this API answers. Capping here rather than in each
client is `data.md` § "Filtering is server-side": the rows the caller discards
are rows nobody had to serialize.

**Zero means no cap, and that is the whole reason this module exists.**
`cli-design.md` § "A sentinel never steals a value the caller can mean" allows
`0` to stand for "all" on a limit, because a row count of nothing is not an
answer anyone asks for. Passing it straight to `Select.limit` does the opposite
— `LIMIT 0` returns an empty set — so `icb tasks list --limit 0` answered with
nothing while `icb overview --limit 0` answered with everything. One helper is
what keeps every endpoint on the same side of that.

A negative limit is rejected at the edge by `ge=0` rather than reaching SQL.
"""

from typing import Annotated

from fastapi import Query
from sqlalchemy import Select

RowLimit = Annotated[
    int | None,
    Query(ge=0, description='Return at most this many rows. Omitted or 0 returns every row.'),
]


def apply_row_limit(query: Select, limit: int | None) -> Select:
    """Cap the query at `limit` rows, or leave it alone when there is no cap.

    Unset and `0` are the same answer — every row — so both leave the query
    untouched rather than reaching `LIMIT 0`.
    """
    if not limit:
        return query
    return query.limit(limit)
