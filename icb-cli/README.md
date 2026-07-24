# icb — the ichrisbirch data CLI

`icb` is a Go/cobra thin REST client over the ichrisbirch FastAPI. It is the
programmatic front door to the personal-productivity apps (tasks, projects,
countdowns, books, articles, habits, events) and the intended **replacement for
the MCP server** — the agent and power-user surface, driven by Claude via Bash or
by a person at the terminal.

It is a per-machine developer tool, not one of the deployed containers. The bash
ops/deploy tool lives at `../cli/icbops` — a different concern in a different
language; the two share no code.

> Design, phased plan, and the reusable build checklist: `.planning/icb-cli.md`.
> Reference build: `~/webapps/nomad/cli/` (this module is copied from it).

## Status

- **Phase 0 (done):** module scaffold + `icb auth {login,logout,status,token}`.
- **Phase 1+ (in progress):** resource command groups (`projects` first, then
  `tasks`, `habits`, `books`, `articles`, `countdowns`, `events`).

End-to-end `icb auth login` additionally requires the homelab Authelia
`icb-cli-<host>` public clients and the ForwardAuth edge routing — a homelab and
per-machine concern, tracked in `.planning/icb-cli.md`.

## Build & install

```bash
make build      # -> ./bin/icb (local testing)
make install    # -> $GOBIN/icb (on your PATH; defaults to ~/go/bin)
make test       # go test ./...
make lint       # go vet + gofmt check
make fmt        # gofmt -w .
```

Install uses `go build -o`, not `go install`: the module path is `ichrisbirch/cli`,
so `go install` would name the binary after the path's last segment (`cli`).

## Auth

`icb auth login` runs Authelia's native OAuth 2.0 Bearer Authorization
(Authorization Code + PKCE + PAR + `form_post` loopback, `gh`-style browser
login). The resulting token is **opaque**, authorized at the Traefik ForwardAuth
edge by audience — the API validates nothing in-process. Tokens live in the OS
keychain (go-keyring), never on disk, and auto-refresh (90-day Authelia `cli`
lifespan). `icb auth token` prints the current access token for scripting:

```bash
curl -H "Authorization: Bearer $(icb auth token)" https://api.ichrisbirch.com/tasks/
```

Client id is per (machine × app): `icb-cli-<shorthostname>`.

## Config (env over default)

| Variable | Default | Purpose |
| --- | --- | --- |
| `ICB_OIDC_ISSUER` | `https://auth.ichrisbirch.com` | Authelia OIDC issuer |
| `ICB_CLIENT_ID` | `icb-cli-<shorthostname>` | per-(machine × app) client id |
| `ICB_OIDC_AUDIENCE` | `https://api.ichrisbirch.com` | token audience (edge-authorized) |
| `ICB_API_BASE` | `https://api.ichrisbirch.com` | API base URL |

## Structure

```text
main.go                    → cli.Execute()
internal/config/           → env-over-default OIDC + API settings
internal/auth/             → OAuth login flow + OS-keychain token store
internal/cli/              → cobra command tree (root, auth; resources to come)
internal/api/              → REST client + wire-contract DTOs (added with Phase 1)
```

The client depends on the JSON **wire contract**, not the server's Python types —
DTOs carry only the fields the CLI renders and ignore unknown fields, so the API
can add columns without breaking the client.
