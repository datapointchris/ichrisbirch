# Running Tests

In order to run pytest, you have to set `ENVIRONMENT=development` so that the config can pick it up and set the correct variables.
Note: Config is not actually setting anything in tests, but the config is called in some of the files that are imported and it will error if not set.

## Dev Testing on Mac

- Make sure to change `/etc/hosts` file:
  `127.0.0.1   localhost` --> `127.0.0.1 localhost api.localhost books.localhost`

Docroot is: /usr/local/var/www

The default port has been set in /usr/local/etc/nginx/nginx.conf to 8080 so that
nginx can run without sudo.

nginx will load all files in /usr/local/etc/nginx/servers/.

To restart nginx after an upgrade:
  brew services restart nginx
Or, if you don't want/need a background service you can just run:
  /usr/local/opt/nginx/bin/nginx -g daemon off;

### `pytest-xdist`

This plugin does not work with the current configuration (08/28/2024) using a local Docker Postgres and running the app, api, and postgres in a separate thread.
`pytest-xdist` bypasses the start of the docker container and all tests fail.
