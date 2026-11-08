# Configuration

## `life/config.py` reads the process environment, after a development or production `.env`

`get_settings()` builds one `Settings` and caches it. Each settings class reads
its keys from `os.environ`, so a required key that is missing fails at startup
with a `KeyError` naming it. `.env.example` lists every required key. An
optional key carries its default in `config.py`.

Before building it, `get_settings()` checks where the environment
`detect_environment()` picks is configured from. That is an explicit
`ENVIRONMENT` first, then `testing` under pytest, then the `ENVIRONMENT` a
`.env` sets, then `development`.

| Environment                 | Configured from                                             | Without it                                                                               |
| --------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `development`, `production` | the checkout's `.env`                                       | the process environment, where it carries `POSTGRES_HOST`; otherwise it refuses to start |
| `testing`                   | the process environment, as set by whatever started the run | it refuses to start without `POSTGRES_HOST`                                              |

A test run is configured from the committed `tests/testing.env`. Importing the
`tests` package loads it into a pytest run, and the test stack's compose file
passes it to each container as its `env_file`. So `life/` names no path
under `tests/`, and a container needs no source tree to read its configuration.
[Testing Configuration](testing/test_configuration.md) covers the file.

The `.env` is named by path from the project root, the directory holding
`pyproject.toml`. python-dotenv's own search climbs from `life/` to the
first `.env` in any parent directory, so a checkout without one would read a
home directory's instead. A file never overrides a variable the process already
holds, so any key can be set for one run without editing a file.
