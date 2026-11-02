# Configuration

## `ichrisbirch/config.py` reads the process environment, after its environment's file

`get_settings()` builds one `Settings` and caches it. Each settings class reads
its keys from `os.environ`, so a required key that is missing fails at startup
with a `KeyError` naming it. `.env.example` lists every key.

Before building it, `get_settings()` loads the file for the environment
`detect_environment()` picks. That is an explicit `ENVIRONMENT` first, then
`testing` under pytest, then the `ENVIRONMENT` a `.env` sets, then
`development`.

| Environment                 | File it loads                  | Without the file                                                                         |
| --------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------- |
| `development`, `production` | the checkout's `.env`          | the process environment, where it carries `POSTGRES_HOST`; otherwise it refuses to start |
| `testing`                   | `tests/testing.env`, committed | it refuses to start                                                                      |

A file never overrides a variable the process already holds, so any key can be
set for one run without editing a file.

### Flake 8

`.flake8` cannot be loaded from `pyproject.toml`
