# icb — the ichrisbirch data CLI

`icb` is a Go/cobra thin REST client over the ichrisbirch FastAPI. It is the
programmatic front door to the personal-productivity apps, which `icb --help`
lists by group, and the **replacement for the retired MCP server** — the agent and power-user surface,
driven by Claude via Bash or by a person at the terminal.

It is a per-machine developer tool, not one of the deployed containers. The bash
ops/deploy tool lives at `../ops/icbops` — a different concern in a different
language; the two share no code.

## What it covers

The apps are `tasks`, `countdowns`, `events`, `habits`, `books`,
`articles`, `autotasks`, `recipes`, `cooking-techniques` and `strains`. Each
takes `{list,show,search,create,edit,delete}` plus the verbs its own domain needs
— `articles current` and `articles read`, `habits complete` and `habits today`,
`tasks snooze`, `pin`, `unpin`, `drop` and `reopen` with `tasks categories` for each
category's window, the recipe suggest/import flows, `recipes vocabulary` and
`strains vocabulary`.

The open task list is ordered by a sort date the CLI never prints: a task's
window in days, counted from when it was added or last snoozed. `tasks list`
shows the position and a pin marker, and `--json` carries the date for a
program that wants it.

`habits today` is the day's board: every habit you currently track, marked done
or still due, ordered by category. It takes no `--limit`, because the set is
what you owe today and a cap can only hide one of them.

`strains` and `recipes` fetch their closed vocabularies rather than compiling
them in. Adding a value is an insert on the server, not a release of this
binary. On `strains`, `--type`, `--status`, `--effect`, `--flavor` and
`--terpene` are all lookup tables, so their values are read from the server on
every create and edit and a wrong one is refused with the list of what would
have worked. `icb strains vocabulary` prints every value with how many strains
carry it. On `recipes`, `icb recipes vocabulary` prints what `--cuisine`,
`--meal-type` and `--difficulty` accept.

`shopping` takes its own verbs, because an item is a catalog row rather than a
record made once. `add` puts names on the list, and a name bought before goes
back in the section it was last in. `check` records a purchase and takes the
item off, `remove` takes it off without one, and `delete` forgets it. `history`
reads the purchase log. `shopping sections` creates, renames, reorders and
deletes the sections. Items and sections are named by name, in any case.

Each machine authenticates as its own Authelia public client, `icb-cli-<host>`.
A new machine needs that client registered in the Authelia configuration before
`icb auth login` will complete.

## Build & install

Run these from the repo root — the Taskfile lives there and enters `cli/` itself.

```bash
task cli:build      # -> ./bin/icb (local testing)
task cli:install    # -> ~/.local/bin/icb, over the released binary
task cli:test       # go test -race ./...
task cli:lint       # go vet + gofmt check
task cli:format     # gofmt -w .
```

Install uses `go build -o`, not `go install`: the module path is `ichrisbirch/cli`,
so `go install` would name the binary after the path's last segment (`cli`).

These build from your working tree, version-stamped with `git describe`. Released
binaries are built by CI on a `cli/v*` tag and published to GitHub Releases; that
is what a machine installs.

## Auth

`icb auth login` runs the OAuth 2.0 device authorization grant (RFC 8628). The
CLI prints a code and a URL; approval happens in any browser on any device,
which is what makes login work over SSH — a loopback redirect needs a browser
that can reach a listener on this machine, and there is none.

The resulting access token is an **RFC 9068 JWT** (`typ: at+jwt`, RS256, `kid:
main`) that the FastAPI verifies itself against Authelia's JWKS. It is not
authorized at the Traefik edge: Authelia forbids the `authelia.bearer.authz`
scope alongside the device grant, so the CLI targets the app's public host. The
`ichrisbirch-bearer` Traefik router carries a request holding an `Authorization`
header past ForwardAuth to FastAPI, so that host serves the CLI without the edge
authorizing the token. That address is the config file's `api` key, and every
request goes to a path under `/api/v1` on it.

Authelia leaves `aud` empty on the device grant and the client-credentials grant
alike, so cross-product isolation rests on the `client_id` claim. The API
requires it to start with `icb-cli-` or `icb-svc-`.

A service runs icb with no person present to approve a login. Its config file
names its confidential client, `icb-svc-<machine>`, as `client_id`, and
`ICB_CLIENT_SECRET` holds that client's secret. A service whose file lacks a key
is told which one to write. icb then requests a token
through the client-credentials grant on each run, asking for
the scopes `config.Service` names, and stores nothing. `auth login` and
`auth logout` refuse in that mode. The API never resolves that token to a user.
It answers 403 on every route its scopes do not list.
`ichrisbirch/api/client_scopes.py` holds that table, and a refused call's message
names the routes its scopes reach.

A workload that gets short-lived tokens from a broker needs no client secret. Its
config file names the broker's command as `token_command`, an argv such as
`["broker", "token", "icb"]`, and needs only `api` beside it. icb runs the
command whenever its last token has expired, and sends the `access_token` it
prints (RFC 6749 § 5.1). The token speaks for the service client that minted it.
`auth status` reports the credential as `external_account`. `auth login` and `auth
logout` refuse, and a 401 names the command rather than a login. A file setting
`token_command` while `ICB_CLIENT_SECRET` is set is refused.

Authelia refuses the whole token request when it names a scope the client does
not hold. So a scope is granted to the client in Authelia before a release of
icb requests it.

The login flow, the keychain store and the refresh are
[goclilogin](https://github.com/datapointchris/goclilogin), shared with the
other product CLIs. Tokens live in the OS keychain, never on disk, and refresh
automatically. That refresh takes a machine-wide lock, because Authelia revokes
the whole grant when two processes replay the same rotated refresh token — the
library's README carries the mechanism.

`icb auth status` reports `live`, `rejected` or `unverified` rather than
predicting a refresh, since a stored token says what this machine holds and not
what Authelia will honor. A rejected session exits 1. The `--json` output names
the credential it checked in `type`, `authorized_user` for a person's login or
`service_account` for a service, as Google's credential files do. A service
stores no token, so its status requests one. It exits 1 unless the provider
grants it.

`icb auth token` prints the current access token for scripting. curl reads the
header from stdin, so the token never appears in another process's arguments:

```bash
printf 'Authorization: Bearer %s\n' "$(icb auth token)" | curl --header @- https://icb.example.com/api/v1/tasks
```

Client id is per (machine × app): `icb-cli-<shorthostname>`.

## `icb overview` — the cross-cutting snapshot

Every other command is `icb <resource> <verb>`. `overview` is the composition
that crosses every app, fetched concurrently and returned as one payload, so a
dashboard needs a single call instead of one per app. `icb overview --help` names
its sections.

Its `habits` section and `icb habits today` answer the same question through one
split, so the two agree on which habits are outstanding. They differ in reach:
`overview` caps each section and `habits today` returns the whole board.

```bash
icb overview                 # the human glance
icb overview --json          # the stable schema, for consumers
icb overview --limit 3       # a tighter per-section cap
```

`--limit 0` returns nothing everywhere it appears, and a negative is a usage
error. What it counts differs by command: a list read caps rows and omitting the
flag returns every one of them, except `shopping history`, whose purchase log
only grows and so comes back capped at its newest rows. `overview` caps each
section separately. Each `--help` names its own unit and default.

Contract notes for consumers (a terminal dashboard is the first):

- `schema_version` is the compatibility signal. Additive changes do not bump it;
  read fields defensively and it stays stable.
- Every capped section reports its pre-cap `total`, so a consumer knows the real
  size of a pile without a second call.
- `warnings` is always an array, each entry keyed by `section`, so one dead
  endpoint degrades one lane instead of the whole snapshot. A rejected session or
  a total failure is *not* a warning — it fails the command, because a partial
  payload would misrepresent an unauthenticated state as an empty one.
- "Done today" matches a completion to its habit by `habit_id`, so a habit
  renamed after being completed stays done. A completion with no `habit_id`
  falls back to name and category.
- "Today" is the day on this machine's calendar: the command sends its zone and
  the server reads the board in it.

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
How soon it should come up. Blank takes the category's window.
Window in days (optional): 14
Notes (optional):
```

The rejected answer comes back on the line for editing, so a typo in the fifth
field never costs the four already typed. Tab walks the choices matching what has
been typed; on an empty line it walks the whole list. A match is a substring
with prefixes ranked first, so `ho` reaches `Home` before `Chore`, and `bisa`
reaches `bisabolol`. A value is matched case-insensitively and stored the way
its source spells it.

A list is laid out in as many columns as its longest entry fits into the
terminal. Under any fixed count, a dozen one-word categories waste most of a
screen and a list of long names wraps.

A flag already passed is never asked about, so `create --category Chore` asks for
name, window, and notes only. Without a terminal — a pipe, a script, or
`--no-input` — nothing is asked and the command names the flags that would have
answered.

`icb strains create` is the same form over fetched choices: its type, status,
effect, flavor and terpene lists come from the server on each run. `Effect`,
`Flavor` and `Terpene` repeat because their flags do, and Enter on an empty one
moves on:

```text
Asked again until you leave it empty.
Effect is one of:
  creative   energetic  euphoric   focused    …
  Tab cycles the matches.
Effect (optional): euphoric
Effect (another, or Enter to move on): foc⇥
Effect (another, or Enter to move on): focused
Effect (another, or Enter to move on):
```

A field with more choices than `maxListedChoices` prints only how many there
are, and Tab is what shows them. There the first Tab on what is typed prints the
matches and the next presses walk them one at a time. That is the shell's habit,
and the only way to read a long list: cycling it a keypress at a time shows one
entry per press and never the shape of the whole. A short vocabulary is already
printed above the prompt, so there Tab walks from the first press.

**The pattern, for the next resource.** One `[]prompt.Field` describes the record:
its label, whether it is optional, whether it repeats or takes prose, its default,
its choices and its validator. That list drives both doors — the fields nothing
answered become the form, and the flags are run through the same validators, so
a bad value reads identically whichever way it arrived — one failure gets one
diagnosis, whichever door it came in by.
`taskCreateFields` in `internal/cli/tasks.go` is the declared-vocabulary
example and `strainCreateFields` in `internal/cli/strains.go` is the fetched one;
`flagAnswers`, `unanswered`, `missingFlags`, `validateAnswers`, and `runForm` in
`internal/cli/interactive.go` are the shared plumbing, and none of them know
anything about tasks or strains.

Where the choices come from an API call, build the client first and check the
required flags before it. A caller that cannot be asked should be told which flag
it left out, not that the API is unreachable.

`internal/prompt` imports nothing from this repo and depends only on
`golang.org/x/term`. Line editing, Tab completion, and the returned-answer
prefill are all `x/term`; there is no TUI framework underneath.

It is staying here. There is no second consumer, and the package is not being
extracted to a shared module.

Copying the directory would not be the whole port in any case.
`internal/cli/interactive.go` is what makes a flag and a prompt one door —
`flagAnswers`, `unanswered`, `missingFlags`, `validateAnswers` and `runForm`.
It depends on nothing in this repo but `internal/prompt` itself, and it sits in
the wrong package to travel with a copy of that directory.

## Config

Where icb is pointed is `$XDG_CONFIG_HOME/icb/config.toml`, read through
goclilogin's config-file contract. It holds three keys, and none has a compiled-in
default:

```toml
api = "https://icb.example.com"
issuer = "https://auth.example.com"
client_id = "icb-cli-laptop"
```

`--api` on any command that reaches the API outranks the file's `api`. With no
file, every such command refuses, naming the file and `icb auth login <url>`. That
login fills in whatever the file lacks — the issuer from the API's RFC 9728
metadata, the client id from `--client-id` or the short hostname — prints each
with where it came from, and writes the file once the login succeeds.
`icb config show` prints the three values, where each came from and the file's
path, as does `icb auth status` beside the session. `icb config path` prints the
path alone, whether or not the file exists.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ICB_CLIENT_SECRET` | unset | a service client's secret; setting it selects the client-credentials grant for the file's `client_id` |

## Structure

```text
main.go                    → cli.Execute()
internal/config/           → OIDC + API settings, and the state directory
internal/cli/              → cobra command tree
internal/api/              → REST client + wire-contract DTOs
internal/prompt/           → the guided-create form (§ Guided create)
```

The client depends on the JSON **wire contract**, not the server's Python types —
DTOs carry only the fields the CLI renders and ignore unknown fields, so the API
can add columns without breaking the client.
