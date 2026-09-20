# Docker Quick Reference

The grammar is `icbops <environment> <verb>`, where the environment is `dev`,
`testing` or `prod`. `test`, `stats`, `routing` and `ssl-manager` are tools
rather than environments. Run any environment with no verb to see its own
listing. `icbops --help` lists all of them.

This page covers the common cases. `--help` is the surface of record.

## URLs

| Environment | App                               | API                               |
| ----------- | --------------------------------- | --------------------------------- |
| Development | `https://app.docker.localhost`    | `https://api.docker.localhost`    |
| Testing     | `https://app.test.localhost:8443` | `https://api.test.localhost:8443` |
| Production  | `https://ichrisbirch.com`         | `https://api.ichrisbirch.com`     |

Every environment goes through Traefik, so these are the addresses to use.
Hitting a container's port on `localhost` skips the proxy. CORS and the auth
middleware live in the proxy, so a request that works there can still fail in
the browser.

## Development

```bash
./ops/icbops dev start
./ops/icbops dev stop
./ops/icbops dev restart
./ops/icbops dev logs api          # follow one service
./ops/icbops dev status            # container state
./ops/icbops dev health            # health checks
./ops/icbops dev smoke             # hit every endpoint
./ops/icbops dev db seed --scale 10
./ops/icbops dev db init
```

`dev logs` persists across restarts, so a container that died on startup still
has readable logs.

## Testing

```bash
./ops/icbops test run                                    # whole suite
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_habits.py
./ops/icbops test run tests/path.py -v -k some_case
./ops/icbops testing start                               # leave the stack up
./ops/icbops testing stop
./ops/icbops testing logs api
./ops/icbops testing db seed --scale 10
./ops/icbops testing db reset                            # drop and recreate
```

`test run` starts the containers if they are not up and waits for health
checks, so it never needs a manual start first.

Every run writes its output to two files under `/tmp`, which are what to read
after a failure instead of re-running the suite. [Testing
troubleshooting](../troubleshooting/testing-issues.md#read-the-output-files-instead-of-re-running)
names them and says what each holds.

## Production

Nothing here deploys. A push to `main` does that.

```bash
./ops/icbops prod deploy-status    # which color is live
./ops/icbops prod status
./ops/icbops prod health
./ops/icbops prod apihealth
./ops/icbops prod logs api
./ops/icbops prod smoke
./ops/icbops prod rollback         # switch traffic to the previous color
./ops/icbops prod build-test       # build the production target locally
```

`prod start` and `prod restart` bring the live color back up, after a reboot
for instance. Both read the active color rather than choosing one.

## Tools

```bash
./ops/icbops routing generate      # after editing vue-paths.txt
./ops/icbops ssl-manager <action> [env]
./ops/icbops stats summary
./ops/icbops install               # symlink to ~/.local/bin/icbops
```

`routing generate` rewrites all three routing files from
`deploy-containers/traefik/vue-paths.txt`. A new Vue route needs an entry there
first, or Traefik routes that path to the API and the page 404s.

## When a change is not taking effect

```bash
./ops/icbops testing stop && ./ops/icbops testing start   # ~30s
./ops/icbops testing rebuild --volumes                    # ~60-90s
```

Work them in that order, and reach for a manual `docker` subcommand only after
both.
[Testing troubleshooting](../troubleshooting/testing-issues.md#a-change-is-not-taking-effect)
says what each step clears and when the heavier `rebuild --all --volumes` is
the right one.

## Environment configuration

One `.env` per environment, loaded by `python-dotenv`, with `ENVIRONMENT` set
to `development`, `testing` or `production`. `.env.example` lists the keys.

Production secrets are SOPS and age encrypted:

```bash
sops secrets/secrets.prod.enc.env
```

[Configuration](../configuration.md) covers precedence and what each key does.

## Things `icbops` does not cover

Docker's own disk usage and cleanup:

```bash
docker system df                   # what is using space
docker system prune -a             # remove unused images and build cache
docker stats                       # live resource usage
```

`prune -a` removes every image not backing a running container, so the next
`dev start` rebuilds from scratch.

## Related

- [Docker Architecture and Build Process](docker.md)
- [Docker Compose Architecture](docker-compose.md)
- [Docker troubleshooting](../troubleshooting/docker-issues.md)
