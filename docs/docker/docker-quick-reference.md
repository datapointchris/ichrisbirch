# Docker Quick Reference

The grammar is `lifeops <environment> <verb>`, where the environment is `dev`,
`testing` or `prod`. `test`, `stats`, `routing` and `ssl-manager` are tools
rather than environments. Run any environment with no verb to see its own
listing. `lifeops --help` lists all of them.

This page covers the common cases. `--help` is the surface of record.

## URLs

| Environment | App                               | API host                          |
| ----------- | --------------------------------- | --------------------------------- |
| Development | `https://app.docker.localhost`    | `https://api.docker.localhost`    |
| Testing     | `https://app.test.localhost:8443` | `https://api.test.localhost:8443` |
| Production  | `https://ichrisbirch.com`         | `https://ichrisbirch.com`         |

Every resource route is under `/api/v1` on the API host; `/health` is at its root.

The testing addresses resolve only inside a checkout's test stack, where the
e2e suite runs. The stack publishes no ports to the host.

Every environment goes through Traefik, so these are the addresses to use.
Hitting a container's port on `localhost` skips the proxy. CORS and the auth
middleware live in the proxy, so a request that works there can still fail in
the browser.

## Development

```bash
./ops/lifeops dev start
./ops/lifeops dev stop
./ops/lifeops dev restart
./ops/lifeops dev logs api          # follow one service
./ops/lifeops dev status            # container state
./ops/lifeops dev health            # health checks
./ops/lifeops dev smoke             # hit every endpoint
./ops/lifeops dev db seed --scale 10
./ops/lifeops dev db init
```

`dev logs` persists across restarts, so a container that died on startup still
has readable logs.

## Testing

```bash
./ops/lifeops test run                                    # whole suite
./ops/lifeops test run tests/life/api/endpoints/test_habits.py
./ops/lifeops test run tests/path.py -v -k some_case
./ops/lifeops testing start                               # leave the stack up
./ops/lifeops testing stop
./ops/lifeops testing logs api
./ops/lifeops testing db seed --scale 10
./ops/lifeops testing db reset                            # drop and recreate
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
./ops/lifeops prod deploy-status    # which color is live
./ops/lifeops prod status
./ops/lifeops prod health
./ops/lifeops prod apihealth
./ops/lifeops prod logs api
./ops/lifeops prod smoke
./ops/lifeops prod rollback         # switch traffic to the previous color
./ops/lifeops prod build-test       # build the production target locally
```

`prod start` and `prod restart` bring the live color back up, after a reboot
for instance. Both read the active color rather than choosing one.

## Tools

```bash
./ops/lifeops routing generate      # after editing vue-paths.txt
./ops/lifeops ssl-manager <action> [env]
./ops/lifeops stats summary
./ops/lifeops install               # symlink to ~/.local/bin/lifeops
```

`routing generate` rewrites all three routing files from
`deploy-containers/traefik/vue-paths.txt`. A new Vue route needs an entry there
first, or Traefik routes that path to the API and the page 404s.

## When a change is not taking effect

```bash
./ops/lifeops testing stop && ./ops/lifeops testing start   # ~30s
./ops/lifeops testing rebuild --volumes                    # ~60-90s
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

## Things `lifeops` does not cover

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
