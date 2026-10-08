# Issues

An issue is a unit of software work, written for the agent that will do it.
Projects hold personal projects. The two are separate stores, so a personal
project is never shaped into a software ticket and development work never
buries the projects list.

`icb issues` is the CLI and `/issues` is the web page. Both read the same API,
under `/issues/`.

## Issues and project items share one number sequence

An issue's `number` comes from the sequence project items also draw from. So
a bare `#42` names exactly one thing across both stores, and a commit message
or a conversation can cite it without saying which.

`id` is the key. `number` is the handle a person or an agent types.

## The ready queue is derived on every read, never stored

An issue is ready when all of these hold:

- it is `open`, or `in_progress` under a claim that has expired
- its not-before day, `deferred_until_date`, has arrived in the reader's calendar
- every issue it depends on is closed
- it has no open children

Every input to that test changes somewhere else. A blocker closes, a claim
expires, a day arrives, a child closes. A stored flag would be wrong the
moment any of them moved, so `services/issue_readiness.py` derives readiness
for every issue in one pass on each read. The API returns it as `is_ready`
and `is_blocked`, and every client filters on those rather than re-deriving
them.

`GET /issues/ready/` is the queue, in the order to take it. `icb issues next`
prints it.

## A decision waits on a person, so the ready queue leaves it out

The `decision` type is the one type that changes what happens to an issue.
It needs a person to choose, and an agent that claimed one could only stall.
The ready queue drops it, and the web page lists decisions under their own
lens.

The other types are `bug`, `feature`, `task` and `chore`. They differ only in
what they say about the work, and `task` is the default.

## Triage holds what nobody has accepted yet

An issue filed as `triage` sits outside the ready queue until someone accepts
it as `open`. Work noticed in passing is filed there, with `discovered_from`
naming the issue it was found during. It is recorded without jumping ahead of
work someone chose.

## Order is effective priority, then rank, then number

Priority uses Linear's scale:

| Value | Name |
| --- | --- |
| 1 | urgent |
| 2 | high |
| 3 | medium |
| 4 | low |
| 0 | none |

`0` is the absence of a priority and sorts after every level.

The priority an issue sorts by is its effective priority:

1. its own priority, when it has one
2. otherwise its open parent's effective priority
3. otherwise its active initiative's priority
4. then raised to the most urgent effective priority of any open issue it blocks

The last step is priority inheritance, from scheduling. Without it a blocker
filed at low priority waits at the bottom while the urgent work it gates sits
at the top of the list, hidden because it is blocked.

`rank` breaks ties inside a priority. It is a float, the way Linear's
`sortOrder` is. A new issue goes one past the last. A move takes the midpoint
of its two new neighbors, so it writes one row. When a move would leave a gap
smaller than `MIN_GAP` in `services/issue_rank.py`, every rank is renumbered to
whole numbers in its current order. `number` breaks a rank tie, because it is
issued in creation order and never repeats.

A move names the issue to sit before or after, and that issue must sort at the
same effective priority. Ranks are one global sequence, so a move beside an
issue of another priority would land wherever the other priorities' ranks fall.
It is refused with a 409 naming both priorities. Changing the priority is what
moves an issue past another priority's.

## A claim is one compare-and-set, and it expires

An agent takes an issue with a claim. One conditional `UPDATE` writes
`claimed_by`, `claim_expires_ts` and `in_progress` together, and matches only
an issue nobody else holds a live claim on. Two agents asking at once never
hold the same issue: the loser's update matches no row. `POST
/issues/ready/claim/` takes the head of the queue this way, moving to the next
candidate when one is lost.

A claim expires. An agent that dies holding work leaves its issue
`in_progress` under a claim that runs out, and the issue then reads as ready
again without anyone releasing it. Claiming again under the same name extends
the claim.

A person can also move an issue to `in_progress` by hand. That carries no
claim and never expires, because a person working on something does not
vanish the way a process does. `DELETE /issues/{n}/claim/` returns either kind
to `open`.

Claiming a named issue applies the ready queue's conditions. An issue the
queue leaves out is refused, so an agent never holds work it could not finish.
Only extending a claim already held skips them.

A refused claim answers 409 naming why. A held issue names who holds it and
until when, so the refused agent can tell whether to wait or move on. Otherwise
the refusal names the open dependencies, the open children or the deferral day.

## Nothing closes an issue for its age

An issue stays open until someone completes or cancels it, however long it
sits. A stale-close bot closes real work that simply has not come up yet, and
the order already decides what gets done next. So age is never an input to
the order or to the status.

Closing is deliberate in both directions:

- **Completed** is refused while the issue has open children, because a parent
  is finished by its children.
- **Canceled** requires a `status_reason` or a `duplicate_of`, so a closed issue
  always says why.
- **Reopen** returns an issue to `open`, and clears when it closed, the reason
  and the duplicate link.

A completed parent never holds open children. A closed issue takes no new open
child, whether filed under it or moved there. Reopening a child returns each
completed ancestor to `open` in the same write.

## Labels are a closed vocabulary with exclusive groups

A label must exist before an issue can carry it, so a misspelling is refused
rather than becoming a second label. Labels sharing a `group_slug` exclude each
other, and an issue carries at most one label from each group.

`/issues/labels` and `icb issues labels` manage the vocabulary.

## An initiative is a bounded outcome

An initiative groups issues toward something with a definition of done, and
lends them its priority. Work with no end is a label instead. An initiative
that can never finish would rank its issues forever by a position nobody
revisits. Only an active initiative lends its priority, so completing or
dropping one stops it ranking the issues still open inside it.

## Not built

- **Due dates.** An issue is ordered by priority and rank, never by a date it
  missed. `deferred_until_date` is the one date, and it only holds an issue
  back.
- **Sprints and estimates.** Both measure a team's throughput against a
  calendar. The queue here is taken one issue at a time in order.
- **Custom workflow states.** The statuses are `triage`, `open`,
  `in_progress`, `completed` and `canceled`. Anything finer is a label.
