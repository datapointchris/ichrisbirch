# Authentication

Every API request resolves to a user, to a scoped client, or to a refusal. The
dependencies that decide which are in `ichrisbirch/api/endpoints/auth.py`.

## Each caller enters through its own door

| Caller | Credential | How it reaches the API |
| --- | --- | --- |
| A person running `icb` | Authelia access token from the device grant | `Authorization: Bearer` to `ichrisbirch.com/api`, which the `ichrisbirch-bearer` router carries past ForwardAuth |
| A service running `icb` | Authelia access token from the client-credentials grant | The same bearer route, with no person present |
| The Vue app in a browser | Authelia session | ForwardAuth on `ichrisbirch.com` injects `Remote-User` and `Remote-Email`; Vue calls `/api/...` on the same origin |
| This app's own services | `X-Service-Key`, with `X-Internal-Service` or with `X-Application-ID` and `X-User-ID` | Internal network |
| A personal API key | `icb_` bearer token | `api.ichrisbirch.com`, which skips ForwardAuth; this path is being retired |
| A local session | JWT this API signs, from `/auth/token/` | `Authorization: Bearer` |

`authenticated_user` runs every user strategy and takes the first match. The
order is the OIDC access token, the Authelia headers, the application headers, a
personal API key, a local JWT, then an OAuth2 form post. FastAPI caches it per
request, so a route that asks for the caller twice looks the user up once.

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
prefix, so `/project-items/{id}/` covers every item.

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

`permits` matches a template exactly. `tests/ichrisbirch/api/test_client_scopes.py`
requests every listed route as a scoped client and requires 200, so a renamed
path parameter fails it with 403.
