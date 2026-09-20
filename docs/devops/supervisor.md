# Supervisor

Supervisor kept the three long-running processes alive when the app ran on bare
metal. One config per process, each naming a gunicorn or python command under
`/var/www/ichrisbirch/.venv/`:

- `app.conf` — `ichrisbirch-app`, gunicorn on `0.0.0.0:8000` with two workers
- `api.conf` — `ichrisbirch-api`
- `scheduler.conf` — `ichrisbirch-scheduler`

Each set `autostart`, `autorestart`, `stopasgroup` and `killasgroup`, so a
restart took the whole process group rather than leaving orphaned workers.

## How it was deployed

`deploy-metal/deploy-supervisor.sh` chose its environment from `uname`, the same
way the NGINX script did. It copied `supervisord.conf` to `$ETC/supervisord.conf`
only when the file differed, which is what kept a needless `supervisord` restart
off an ordinary config deploy. The three program configs went to
`$ETC/supervisor/conf.d/` as `ichrisbirch-<name>.conf`, and it touched the four
log files under `/var/log/supervisor/` so supervisord would not fail on a
missing path.

`--dry-run` printed every path and exited.

!!! warning "Not the current deploy path"
    Docker supervises these processes now. `api`, `vue` and `scheduler` are
    services in `docker-compose.app.yml` with their own restart policies, and
    the blue/green deploy swaps `icb-blue` and `icb-green` rather than
    restarting a process in place. Nothing reads these supervisor configs.

    See [Blue/Green Deployment](../blue-green-deployment.md) for what replaced
    it.

The files are kept because they record the worker counts and the process-group
semantics the container deploy had to match. They sit in
`deploy-metal/{dev,prod}/supervisor/`, with an identical copy under
`deploy-containers/`.
