# Authentication

Every API request resolves to a user, to a scoped client, or to a refusal. The
dependencies that decide which are in `ichrisbirch/api/endpoints/auth.py`.

## Each caller enters through its own door

| Caller | Credential | How it reaches the API |
| --- | --- | --- |
| A person running `icb` | Authelia access token from the device grant | `Authorization: Bearer` to `ichrisbirch.com/api/v1`, which the `ichrisbirch-bearer` router carries past ForwardAuth |
| A service running `icb` | Authelia access token from the client-credentials grant | The same bearer route, with no person present |
| The Vue app in a browser | Authelia session | ForwardAuth on `ichrisbirch.com` injects `Remote-User` and `Remote-Email`; Vue calls `/api/v1/...` on the same origin |
| This app's own services | `X-Service-Key`, with `X-Internal-Service` or with `X-Application-ID` and `X-User-ID` | Internal network |

`authenticated_user` runs every user strategy and takes the first match. The
order is the OIDC access token, the Authelia headers, then the application
headers. FastAPI caches it per request, so a route that asks for the caller
twice looks the user up once.

The API signs no token of its own and accepts no password. A user row keeps its
password hash, and no strategy reads it.

## An access token is verified here, not at the edge

The device grant cannot request Authelia's `authelia.bearer.authz` scope, so
Traefik cannot authorize these tokens. `ichrisbirch/api/oidc_auth.py` verifies
them in-process instead, against Authelia's JWKS:

- the header `typ` is `at+jwt`, which is what keeps an id_token from the same
  issuer out;
- the RS256 signature matches a published key;
- `iss` matches `OIDC_ISSUER`, and `exp` is in the future;
- `client_id` starts with this product's CLI or service prefix.

Authelia leaves `aud` empty on both grants, so the `client_id` prefix is what
keeps another product's token out.

A token that fails any check answers one opaque 401 and never falls through to
a weaker strategy. Otherwise a junk token sent beside a forged `Remote-User`
header would be ignored, and the request would run as that header's user.

## The issuer is published without a credential

`icb auth login <url>` learns which issuer to log in through from the API's RFC
9728 metadata, before it holds a token. `ichrisbirch/api/protected_resource.py`
serves `{"resource": PUBLIC_URL, "authorization_servers": [OIDC_ISSUER]}` with no
authentication, and serves nothing while `PUBLIC_URL` is unset. The CLI refuses
the document unless `resource` matches the URL it was given exactly, so
`PUBLIC_URL` is set per deployment rather than derived from a request.

The resource is `https://ichrisbirch.com`, so RFC 9728 puts its document at
`/.well-known/oauth-protected-resource`, beside `/api`. The prod router
`api-root` carries that path to the API, and the edge needs a router of its own
for it, since a request without a token otherwise meets ForwardAuth.

## Remote-User is read only where ForwardAuth set it

The edge runs ForwardAuth on `ichrisbirch.com`, and one kind of request reaches
the API without it. The `ichrisbirch-bearer` router carries any
`ichrisbirch.com` request holding `Authorization: Bearer` past it. On such a
request, a `Remote-User` header came from the client.

Two rules close it in this repo, whatever the edge does:

- The prod Traefik blanks `Remote-User`, `Remote-Email`, `Remote-Name` and
  `Remote-Groups` on every router except `api-proxy`. A router added later
  takes that middleware unless ForwardAuth runs in front of it.
- The header strategy returns None for any request carrying an `Authorization`
  header, whatever that header holds.

So a bearer token no strategy accepts answers 401 rather than resolving the
headers. A valid one runs as its own user, even beside an admin's headers. A
bearer that is not an access token passes the OIDC strategy by. Without the
second rule, the request would then run as the account the headers named.
`tests/ichrisbirch/api/test_authelia_headers.py` holds both cases.

## The client_id prefix decides whether a token is a person or a scoped client

`icb-cli-<machine>` is a person. The token must carry a non-empty `sub`, and it
resolves to the user `OIDC_CLI_USER_EMAIL` names.

`icb-svc-<machine>` is a service running the CLI. The token must carry a
non-empty `scp` list, and it becomes a `ScopedClient` that never resolves to
any user.

A missing `sub` cannot decide this. Authelia 4.39 leaves `sub` off a
client-credentials token, but RFC 9068 requires one. A release that adds it
would make a service token look like a person's, and every person's token here
acts as the account owner.

## A scoped client reaches only the routes its scopes list

`ichrisbirch/api/client_scopes.py` maps each scope to the
`(method, route template)` pairs it reaches. A template includes the router
prefix, so `/api/v1/project-items/{id}` covers every item.

A router with a route in `SCOPE_ROUTES` takes
`get_current_user_or_scoped_client`. It admits a scoped client only on a listed
route, and resolves everyone else exactly as `get_current_user` does. The other
routers that authenticate at the router take `get_current_user`, or
`get_admin_user`, which depends on it. Every other dependency that resolves a
user refuses a scoped client with 403. That holds when the request also sends a
`Remote-User` header, which the header strategy would otherwise resolve to that
account.

A handler that resolves the user through its own dependency refuses a scoped
client too. `RequestZone` takes `get_current_user_or_scoped_client` for that
reason, and a scoped client that names no `timezone` gets UTC.

**`icb.issues.close` writes, and the handler narrows it to a close.** It lists
the comment route and the issue update, which is what a scheduled job sends to
complete an issue once its fix merged. A route permits by method and template,
never by body, so the update handler narrows a scoped client's body naming
`status` or `closed_by` to those two fields, a closing status, and an issue
still open. A close naming no closer is stamped with the client's id.
*Rejected:* `icb.issues.write`, which reads as every write route, and a
dedicated close route, which would be a second way to close beside the update.

**`icb.issues.claim` holds an issue, and the handlers narrow it to the client's
own claim.** It lists the claim and release of a named issue, which a scheduled
job sends to keep an issue out of the ready queue while its fix agent carries it.
Release frees whoever holds an issue, so a scoped client's claim must name its
own client id, and its release is refused on an issue another claimant holds or
a person set in progress. The queue's own claim, which takes the head of the
queue, is not listed, because the job names the issue it files. *Rejected:*
stamping the client id over whatever claimant the body names, which would print
one claimant to the caller and store another.

**`icb.issues.plan` orders the queue, and the handlers narrow its edit to
priority and initiative.** It lists the issue update, the rank move, filing an
issue, and creating and updating an initiative. That is what a scheduled
planning job sends to re-tier the queue, regroup it and re-rank it. Filing reads
the vocabulary first, so that read is listed too. Nothing under it deletes, and
it lists no comment, because the job writes none.

The issue update is listed under both scopes, so the handler picks the narrowing
from the body. A body naming `status` or `closed_by` is a close, and meets the
close's narrowing when the client holds `icb.issues.close`. Every other body, and
a close from a client holding only `icb.issues.plan`, may set only `priority`
and `initiative`. So a client holding both is refused an update that sets a
title. An initiative's update is not narrowed: the scope that completes and
drops one also renames it and reopens it.

A scoped client files only into triage, and under no parent. Triage holds the
issue until a person accepts it, so a job's filing never reaches the ready queue
on its own. A parent waits on each of its open children, so a filing naming one
would take an issue already in the queue out of it.

`permits` matches a template exactly. `tests/ichrisbirch/api/test_client_scopes.py`
requests every listed route as a scoped client and requires its success status,
so a renamed path parameter fails it with 403.

A refused scoped client's 403 message names the routes its scopes reach. The same
test file writes the table to `tests/ichrisbirch/api/testdata/client-scopes.json`.
The CLI's suite runs each call a scheduled job makes as a service, in
`TestService_EachScheduledCallSendsARouteTheRequestedScopesReach`, and requires
every request it sends to match a route listed there for a scope the CLI
requests. A `{name:path}` template matches any segments, as FastAPI's path
converter does, because a job names an initiative by its name.
