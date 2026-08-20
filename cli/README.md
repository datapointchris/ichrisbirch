# icb — the ichrisbirch data CLI

`icb` is a Go/cobra thin REST client over the ichrisbirch FastAPI. It is the
programmatic front door to the personal-productivity apps (tasks, projects,
countdowns, books, articles, habits, events, recipes, cooking-techniques) and the
**replacement for the retired MCP server** — the agent and power-user surface,
driven by Claude via Bash or by a person at the terminal.

It is a per-machine developer tool, not one of the deployed containers. The bash
ops/deploy tool lives at `../ops/icbops` — a different concern in a different
language; the two share no code.

> Reference build: `~/webapps/nomad/cli/` (this module is copied from it).

## Status

- **Phase 0 (done):** module scaffold + `icb auth {login,logout,status,token}`.
- **Phase 1 (done):** the Projects domain — `icb projects`
  ({list,show,create,edit,complete,drop,reopen,delete}; create and edit refuse a
  name the repo registry knows, since a project name is bounded work and a repo
  does not end) and `icb projects items`
  (project-item CRUD, complete/reopen, archive/unarchive, reorder,
  multi-project membership,
  dependencies + blockers, `tree` for the dependency graph as a drawing or as
  nodes and edges in `--json`, and sub-task verbs). Items are only meaningful inside
  a project, so the group is nested rather than a root noun; `icb projects items
  list --project <id>` is the in-order listing for one project.
- **Phase 2 (done):** the standalone apps — `tasks`, `countdowns`, `events`,
  `habits`, `books`, and `articles` ({list,show,search,create,edit,delete} plus
  resource-specific verbs: `articles current`/`read`, `habits complete`, etc.).
- **Phase 3 (done, 2026-07-24):** MCP parity + retirement. `icb` covers the full
  ~78-tool surface (parity additions: `autotasks`, `articles` bulk-import,
  `cooking-techniques`, and `recipes` incl. the AI suggest/import flows). The
  homelab Authelia `icb-cli-{host}` clients are deployed, `icb auth login` works
  end-to-end against production, and the **MCP server has been retired**. The
  `api.ichrisbirch.com` bypass is kept — it is the Personal API Key access path,
  not MCP-specific, and it is now also the host `icb` itself targets.
- **Phase 4 (done):** `Makefile` (build/install/test/lint/fmt) + a CI **Test CLI**
  job gated on the `cli/**` path filter (not in the deploy gate).

The homelab Authelia `icb-cli-<host>` public clients are deployed and `icb auth
login` works end-to-end; a fresh machine only needs its `icb-cli-<host>` client
added to the Authelia config (see
`~/homelab/pyinfra/templates/authelia/configuration.yml.j2`).

## Build & install

Run these from the repo root — the Taskfile lives there and enters `cli/` itself.

```bash
task cli:build      # -> ./bin/icb (local testing)
task cli:install    # -> $GOBIN/icb (falls back to $GOPATH/bin)
task cli:test       # go test -race ./...
task cli:lint       # go vet + gofmt check
task cli:fmt        # gofmt -w .
```

Install uses `go build -o`, not `go install`: the module path is `ichrisbirch/cli`,
so `go install` would name the binary after the path's last segment (`cli`).

These build from your working tree, version-stamped with `git describe`. Released
binaries are built by CI on a `cli/v*` tag and published to GitHub Releases; that
is what dotfiles installs on each machine.

## Auth

`icb auth login` runs the OAuth 2.0 device authorization grant (RFC 8628). The
CLI prints a code and a URL; approval happens in any browser on any device,
which is what makes login work over SSH — a loopback redirect needs a browser
that can reach a listener on this machine, and there is none.

The resulting access token is an **RFC 9068 JWT** (`typ: at+jwt`, RS256, `kid:
main`) that the FastAPI verifies itself against Authelia's JWKS. It is not
authorized at the Traefik edge: Authelia forbids the `authelia.bearer.authz`
scope alongside the device grant, so the CLI targets `api.ichrisbirch.com`,
which bypasses ForwardAuth and reaches FastAPI directly.

Authelia does not carry the audience through the device grant — `aud` comes
back empty — so cross-product isolation rests on the `client_id` claim, and the
API requires it to start with `icb-cli-`.

Tokens live in the OS keychain (go-keyring), never on disk, and auto-refresh
(90-day Authelia `cli` lifespan). `icb auth token` prints the current access
token for scripting:

```bash
curl -H "Authorization: Bearer $(icb auth token)" https://api.ichrisbirch.com/tasks/
```

Client id is per (machine × app): `icb-cli-<shorthostname>`.

## `icb overview` — the cross-cutting snapshot

Every other command is `icb <resource> <verb>`. `overview` is the one composition
command: open tasks, habits still due today, current and next reading, next and
blocked project items, and approaching countdowns and events — fetched
concurrently and returned as one payload, so a dashboard needs a single call
instead of nine.

```bash
icb overview                 # the human glance
icb overview --json          # the stable schema, for consumers
icb overview --limit 0       # no per-section cap
```

Contract notes for consumers (`menu dashboard` in dotfiles is the first):

- `schema_version` is the compatibility signal. Additive changes do not bump it;
  read fields defensively and it stays stable.
- Every capped section reports its pre-cap `total`, so a consumer knows the real
  size of a pile without a second call.
- `warnings` is always an array, each entry keyed by `section`, so one dead
  endpoint degrades one lane instead of the whole snapshot. A rejected session or
  a total failure is *not* a warning — it fails the command, because a partial
  payload would misrepresent an unauthenticated state as an empty one.
- Habit completions carry no habit id, so "done today" matches on name and
  category. A habit renamed after being completed today reads as due again until
  its next completion.

## Guided create — `internal/prompt`

`icb tasks create` with `--name` or `--category` missing asks for the rest of the
record one field at a time, rather than refusing:

```text
Creating a task. Ctrl-C to abandon it.

Name: Renew registration
Category is one of:
  Automotive  Chore  Computer  Dingo     Financial  Home
  Kitchen     Learn  Personal  Purchase  Research   Work
  Tab cycles the matches.
Category: chorre
  unknown value "chorre" — one of: Automotive, Chore, Computer, ...
Category: chore
Priority is a rank — lower comes first.
Priority [1]: 3
Notes (optional):
```

The rejected answer comes back on the line for editing, so a typo in the fifth
field never costs the four already typed. Tab walks the choices matching what has
been typed; on an empty line it walks the whole list. A match is a substring
with prefixes ranked first, so `ho` reaches `Home` before `Chore`, and a project
called `Convert theme and font from bash to Go` is reached by typing `theme`. A
value is matched case-insensitively and stored the way its source spells it.

A list is laid out in as many columns as its longest entry fits into the
terminal. A dozen one-word categories waste most of a screen stacked four wide,
and a project whose name is a sentence wraps in that many.

A flag already passed is never asked about, so `create --category Chore` asks for
name, priority, and notes only. Without a terminal — a pipe, a script, or
`--no-input` — nothing is asked and the command names the flags that would have
answered.

`icb projects items create` is the same form over fetched choices. There are
more projects and more repos than fit above a prompt, so neither list is printed
unasked — the field says how many there are and Tab is what shows them:

```text
Project — 54 to choose from; Tab lists them, or type any part of one first to narrow it.
  + makes a new project.
Project: ⇥
  Adjust the wooden dingo run              Blue green hardening
  Convert theme and font from bash to Go   fleet facts — the measurement layer
  ⋮
Project: theme⇥
Project: Convert theme and font from bash to Go
Project (another, or Enter to move on):
Repo — 82 to choose from; Tab lists them, or type any part of one first to narrow it.
Repo (optional): dotfiles
Notes — one or more lines, blank line ends it:
  > the reasoning that has to outlive the commit
  >
```

The first Tab on what is typed prints the matches; the next presses walk them
one at a time. That is the shell's habit and it is the only way to read a list
this long — cycling it a keypress at a time shows one project per press and
never the shape of the whole. A short vocabulary is already printed above the
prompt, so there Tab walks from the first press. `maxListedChoices` decides
both: what the field could not introduce is what Tab introduces.

`Project` repeats because `--project` is repeatable — Enter on an empty one moves
on. `Notes` takes as many lines as it is given, which is where an item's
reasoning goes. A project is accepted by name or by id, since the API resolves
either and only the names can be offered as choices.

**Making the missing project without losing the item.** Answering `Project` with
`+` asks for a name, a description and a kind, creates the project, and carries
on filing:

```text
Project: +
New project. Enter on an empty name goes back to picking one.
Name: Zebra crossing overhaul
What the effort covers. A project without one collects the wrong items later.
Description (optional): the crossing rebuild and everything it drags in
Kind is one of:
  build  chore  life
  Tab cycles the matches.
Kind [build]: build
  Created project "Zebra crossing overhaul".
Project (another, or Enter to move on):
```

The missing project is discovered while filing an item, which is the worst
moment to leave: quitting to run `projects create` loses the half-typed item. An
empty name backs out and makes nothing, so a `+` pressed by mistake is not a
Ctrl-C that abandons the item too. The repo-named-project ban runs on the name
here exactly as it does behind `--name` — a form is not a way around it.

This is `prompt.Escape`, and it is the general shape rather than a project
thing: a `Trigger` answer, a `Hint` printed with the choices, and a `Run` that
makes the value. What `Run` returns is the answer unvalidated, joins the field's
choices for the next repeat, and is accepted case-insensitively if it is typed
again — the escape made the value, so it is the authority on it, and a validator
built before it existed has nothing to say.

**The pattern, for the next resource.** One `[]prompt.Field` describes the record:
its label, whether it is optional, whether it repeats or takes prose, its default,
its choices, its validator, and its escape. That list drives both doors — the
fields nothing answered become the form, and the flags are run through the same
validators, so a bad value reads identically whichever way it arrived
(`standards/cli-design.md` § "One failure, one diagnosis, whichever door you came
in"). The escape is the one part only the form has: `--project` still refuses a
name that does not exist, because a flag has nobody to ask what kind it is. `taskCreateFields` in `internal/cli/tasks.go` is the declared-vocabulary
example and `itemCreateFields` in `internal/cli/items.go` is the fetched one;
`flagAnswers`, `unanswered`, `missingFlags`, `validateAnswers`, and `runForm` in
`internal/cli/interactive.go` are the shared plumbing, and none of them know
anything about tasks or items.

Where the choices come from an API call, build the client first and check the
required flags before it. A caller that cannot be asked should be told which flag
it left out, not that the API is unreachable.

`internal/prompt` imports nothing from this repo and depends only on
`golang.org/x/term`. Line editing, Tab completion, and the returned-answer
prefill are all `x/term`; there is no TUI framework underneath.

It is not going anywhere, though. The fleet's other CLIs were surveyed on
2026-08-19 and none of them wants this — see `.planning/status.md` § "Not
Doing", which carries the survey so it is not run again. Copying the directory
would not have been the whole port in any case: `internal/cli/interactive.go`
is what makes the flags and the form one door, it depends on nothing in this
repo either, and it sits in the wrong package to travel with a directory copy.

## Config (env over config file over default)

| Variable | Default | Purpose |
| --- | --- | --- |
| `ICB_OIDC_ISSUER` | `https://auth.ichrisbirch.com` | Authelia OIDC issuer |
| `ICB_CLIENT_ID` | `icb-cli-<shorthostname>` | per-(machine × app) client id |
| `ICB_API_BASE` | `https://api.ichrisbirch.com` | API base URL |
| `ICB_REPOS_REGISTRY` | `$XDG_DATA_HOME/icb/repos.json` | repo registry `--repo` and `projects create` validate against |

The registry is the one file icb reads that other tools also read, so it resolves
through three rungs rather than two: `$ICB_REPOS_REGISTRY`, then `repos_registry`
in `$XDG_CONFIG_HOME/icb/config.yml`, then the default above. A leading `~`
expands in either declared layer.

```yaml
# $XDG_CONFIG_HOME/icb/config.yml
repos_registry: ~/dev/repos.json
```

The config file is optional. A machine keeping the registry where icb expects it
needs none, and an unreadable or malformed one falls through to the default
rather than failing the command.

No unprefixed variable is read. `$REPOS_JSON` was the rung below the config and
came out: it is exported from a shell profile, so a process that sources none —
a systemd timer, anything unattended — never saw it, and the rung was empty in
exactly the runs it existed to serve.

## Structure

```text
main.go                    → cli.Execute()
internal/config/           → OIDC + API settings, and the machine config file
internal/auth/             → OAuth login flow + OS-keychain token store
internal/cli/              → cobra command tree
internal/api/              → REST client + wire-contract DTOs
internal/prompt/           → the guided-create form (§ Guided create)
internal/graph/            → dependency-graph layout for `projects items tree`
internal/repos/            → the machine's repo registry, for --repo validation
```

The client depends on the JSON **wire contract**, not the server's Python types —
DTOs carry only the fields the CLI renders and ignore unknown fields, so the API
can add columns without breaking the client.
