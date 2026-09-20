# NGINX

NGINX was the reverse proxy when the app ran on bare metal. It terminated TLS
with the Let's Encrypt certificate for `ichrisbirch.com`, then proxied `/` to
gunicorn on a local port — 8200 for the API, 8000 for the app.

Two files did the routing, one per host name:

- `api.conf` — `api.ichrisbirch.com`, a 301 from port 80 and a proxy on 443
- `app.conf` — the app host, same shape

Both set the WebSocket upgrade headers and a 86400-second read timeout, because
a long-lived WebSocket otherwise dies at the proxy's default.

## How it was deployed

`deploy-metal/deploy-nginx.sh` picked its environment from `uname`. Darwin meant
dev under a `/usr/local` prefix; anything else meant prod with no prefix. It
then copied `nginx.conf` to `$ETC/nginx/`, copied each site config into
`sites-available` as `ichrisbirch-<name>.conf`, symlinked those into
`sites-enabled`, and ran `nginx -s reload`.

`--dry-run` printed every path it would write and exited without touching
anything.

!!! warning "Not the current deploy path"
    Traefik is the reverse proxy now, and it runs as the `traefik` service in
    `docker-compose.yml`. It terminates TLS, routes by host and carries the CORS
    and security middlewares. Nothing reads these NGINX configs.

    Routing changes go through `deploy-containers/traefik/` and
    `icbops routing generate`. Running `deploy-nginx.sh` against a production
    host would write config for a server that is not installed.

The files are kept because they record the port layout and the WebSocket
timeout that the container deploy had to reproduce. They sit in
`deploy-metal/{dev,prod}/nginx/`, with an identical copy under
`deploy-containers/`.
