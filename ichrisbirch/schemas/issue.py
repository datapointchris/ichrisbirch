from datetime import date
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import StringConstraints
from pydantic import model_validator

from ichrisbirch.schemas.not_null import NotNull

# What a caller may pass where an issue or an initiative is named. An issue
# answers to its UUID or its number, an initiative to its UUID or its name, and
# the API resolves either. `str` is in the issue union because a CLI forwards
# what was typed, so a number arrives as "42".
IssueRef = UUID | int | str
InitiativeRef = UUID | str

Priority = Annotated[int, Field(ge=0, le=4, description='0 none, 1 urgent, 2 high, 3 medium, 4 low')]
Slug = Annotated[str, StringConstraints(pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$')]
Claimant = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ClaimMinutes = Annotated[int, Field(ge=1, le=10080, description='How long the claim holds before the issue is ready again')]

DEFAULT_CLAIM_MINUTES = 240


class IssueConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IssueSummary(IssueConfig):
    """Enough of another issue to print it beside this one without fetching it."""

    id: UUID
    number: int
    title: str
    status: str


class InitiativeSummary(IssueConfig):
    id: UUID
    name: str
    status: str
    priority: int


class IssueCreate(IssueConfig):
    """`status` takes `triage` for work filed by a machine, which waits there until accepted."""

    title: str
    description: str | None = None
    acceptance: str | None = None
    repo: str | None = None
    type: str = 'task'
    status: str = 'open'
    priority: Priority = 0
    deferred_until_date: date | None = None
    initiative: InitiativeRef | None = None
    parent: IssueRef | None = None
    discovered_from: IssueRef | None = None
    labels: list[Slug] = []
    depends_on: list[IssueRef] = []


class IssueUpdate(IssueConfig):
    """Status moves through here, and the server stamps what a transition implies.

    `closed_ts` and the claim are never sent: closing stamps the one and clears
    the other. `duplicate_of` is accepted only alongside `status: canceled`, and
    `labels` replaces the issue's whole set.
    """

    title: NotNull[str] = None
    description: str | None = None
    acceptance: str | None = None
    repo: str | None = None
    type: NotNull[str] = None
    status: NotNull[str] = None
    status_reason: str | None = None
    priority: NotNull[Priority] = None
    deferred_until_date: date | None = None
    initiative: InitiativeRef | None = None
    parent: IssueRef | None = None
    discovered_from: IssueRef | None = None
    duplicate_of: IssueRef | None = None
    labels: NotNull[list[Slug]] = None


class Issue(IssueConfig):
    """An issue travels with everything a list row needs, so no client fans out.

    `effective_priority` is the priority the ready queue sorts by: the issue's
    own, else its parent's or its active initiative's, raised to the most urgent
    of anything it blocks. `is_ready` says whether an agent could take it now,
    whatever its type; the ready queue leaves decisions out separately.
    """

    id: UUID
    number: int
    title: str
    description: str | None = None
    acceptance: str | None = None
    repo: str | None = None
    type: str
    status: str
    status_reason: str | None = None
    priority: int
    effective_priority: int
    rank: float
    deferred_until_date: date | None = None
    claimed_by: str | None = None
    claim_expires_ts: datetime | None = None
    initiative: InitiativeSummary | None = None
    parent: IssueSummary | None = None
    discovered_from: IssueSummary | None = None
    duplicate_of: IssueSummary | None = None
    labels: list[str] = []
    depends_on: list[IssueSummary] = []
    blocks: list[IssueSummary] = []
    child_count: int = 0
    open_child_count: int = 0
    comment_count: int = 0
    is_blocked: bool
    is_ready: bool
    created_ts: datetime
    updated_ts: datetime
    closed_ts: datetime | None = None


class IssueCommentCreate(IssueConfig):
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    author: str | None = None


class IssueComment(IssueConfig):
    id: UUID
    issue_id: UUID
    body: str
    author: str | None = None
    created_ts: datetime


class IssueDetail(Issue):
    children: list[IssueSummary] = []
    comments: list[IssueComment] = []


class IssueDependencyCreate(IssueConfig):
    depends_on: IssueRef


class IssueClaimRequest(IssueConfig):
    claimant: Claimant
    minutes: ClaimMinutes = DEFAULT_CLAIM_MINUTES


class IssueReadyClaimRequest(IssueClaimRequest):
    """Take the head of the ready queue, narrowed by the same filters the queue reads."""

    repo: str | None = None
    type: str | None = None
    label: Slug | None = None
    initiative: InitiativeRef | None = None


class IssueClaimResult(IssueConfig):
    """`issue` is null when nothing was ready to claim, which is not an error."""

    issue: Issue | None = None


class IssueRankMove(IssueConfig):
    """Place an issue immediately before or after another of the same effective priority."""

    before: IssueRef | None = None
    after: IssueRef | None = None

    @model_validator(mode='after')
    def exactly_one_neighbor(self):
        if (self.before is None) == (self.after is None):
            raise ValueError('give exactly one of before or after')
        return self


class InitiativeCreate(IssueConfig):
    name: str
    description: str | None = None
    status: str = 'active'
    status_reason: str | None = None
    priority: Priority = 0
    position: int | None = None


class InitiativeUpdate(IssueConfig):
    """`closed_ts` is stamped on the move into a terminal status and cleared on reopen."""

    name: NotNull[str] = None
    description: str | None = None
    status: NotNull[str] = None
    status_reason: str | None = None
    priority: NotNull[Priority] = None
    position: NotNull[int] = None


class Initiative(IssueConfig):
    """An initiative and the counts that say whether work is left in it.

    The three counts partition `issue_count`. `repos` is derived from every issue
    not canceled, never stored, so it cannot drift from what the work touches.
    """

    id: UUID
    name: str
    description: str | None = None
    status: str
    status_reason: str | None = None
    priority: int
    position: int
    created_ts: datetime
    closed_ts: datetime | None = None
    issue_count: int = 0
    open_count: int = 0
    completed_count: int = 0
    canceled_count: int = 0
    repos: list[str] = []


class IssueLabelCreate(IssueConfig):
    slug: Slug
    group_slug: Slug | None = None
    description: str | None = None


class IssueLabelUpdate(IssueConfig):
    """The slug is the key and never changes; renaming is delete plus create."""

    group_slug: Slug | None = None
    description: str | None = None


class IssueLabel(IssueConfig):
    slug: str
    group_slug: str | None = None
    description: str | None = None
    open_issue_count: int = 0


class IssuePriorityName(IssueConfig):
    value: int
    name: str


class IssueVocabulary(IssueConfig):
    """Every value a closed issue field accepts, for a client building its pickers."""

    statuses: list[str]
    types: list[str]
    priorities: list[IssuePriorityName]
    initiative_statuses: list[str]
    labels: list[IssueLabel]
