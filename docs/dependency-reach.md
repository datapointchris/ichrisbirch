# What a Dependency Can Reach

These dependencies see more than the code that calls them, so what each one reaches is written down here rather than inferred from the import. Add a dependency here when it receives user content, makes outbound requests, or holds a handle on the host.

## claude-agent-sdk

`claude-agent-sdk` receives user content, not metadata, and is the only model provider the app talks to. `ichrisbirch/ai/assistants/anthropic.py` wraps it; the callers are `api/endpoints/articles.py`, `api/endpoints/recipes.py` and `services/url_ingest.py`. Each call runs the Claude Code CLI bundled in the package, authenticated by the subscription OAuth token in `AI_ANTHROPIC_OAUTH_TOKEN`, so usage draws on the Claude plan and never on API credits. `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` outrank that token inside Claude Code, so `options()` blanks both on every call. What crosses the boundary is the full text of a saved article, a recipe being imported, and the contents of any URL ingested.

The CLI inherits the API process's whole environment, which is the decrypted `.env`: the database and Redis passwords, the internal service key, the Slack webhook and the default users' passwords, beside the OAuth token. That is accepted. The model has no tool that reads the environment, and every library in the API process already holds the same values, so a compromised CLI binary reaches what a compromised Python dependency would. The CLI's nonessential traffic, analytics included, is switched off on every call. It loads no CLAUDE.md, settings, skills or MCP servers, and the only tool any call has is `WebSearch`, on recipe discovery, capped at five calls.

## docker

`docker` is a *runtime* dependency, and `api/endpoints/admin.py` builds a client with `docker.from_env()` to report container status on the admin page. That gives the API process a handle on the host daemon, which is the widest reach in the list: a daemon socket is root-equivalent on the host. It is narrow in use — status reads only — and the endpoint is behind `get_admin_user`.

## testcontainers

`testcontainers` is a *test* dependency, used only by `PrivateServices` in `tests/environment.py`. It reaches the Docker daemon through the same socket the `docker` client uses, so a pytest process holds the root-equivalent handle a developer's own shell already has. Each session starts three containers: the Postgres and Redis images production runs, read from `docker-compose.yml`, and the `testcontainers/ryuk` reaper. Ryuk mounts the daemon socket read-write, so it can remove the session's containers when the session dies. It is unprivileged unless `TESTCONTAINERS_RYUK_PRIVILEGED` says otherwise. Nothing from the app's `.env` reaches any of the three: the database runs with fixed test credentials, and Redis without a password.

## curl_cffi

`curl_cffi` makes every third-party page request, from `services/outbound_http.py`. It reaches whatever URL a user saved, as any HTTP client would, and carries nothing but the request.

## trafilatura and pypdf

`trafilatura` and `pypdf` parse page and PDF bytes already fetched, in `services/url_extraction.py`. Neither makes a request: `trafilatura`'s own download helpers are never called.

## yt-dlp and youtube-transcript-api

`yt-dlp` fetches YouTube metadata on the app's behalf from `services/url_extraction.py`, alongside `youtube-transcript-api`. Both make outbound requests to a third party with whatever URL a user saved. `yt-dlp` releases weekly to track site changes, so it carries a lower bound only.
