#!/usr/bin/env bats
#
# The Vue server answers every path that is not a built file with index.html,
# and a browser holding an old copy of it keeps loading the old bundle, so none
# of those paths may be cached. Caddy runs `header` before `try_files` rewrites
# the path, so a matcher on /index.html never sees a request for / or /today.
# This runs the production Caddyfile in the image the Vue Dockerfile serves
# from, against a stand-in build.

setup_file() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  local image srv
  image=$(sed -n 's/^FROM \(caddy:[^ ]*\).*/\1/p' "$REPO_ROOT/frontend/Dockerfile")
  srv="$BATS_FILE_TMPDIR/srv"
  mkdir -p "$srv/assets"
  echo '<!doctype html><title>entry</title>' >"$srv/index.html"
  echo 'console.log(1)' >"$srv/assets/index-abc123.js"
  echo '{}' >"$srv/manifest.webmanifest"

  CONTAINER="icb-caddy-cache-$$"
  export CONTAINER
  docker run --rm -d --name "$CONTAINER" -p 127.0.0.1::80 \
    -v "$REPO_ROOT/frontend/Caddyfile:/etc/caddy/Caddyfile:ro" \
    -v "$srv:/srv:ro" "$image" >/dev/null
  PORT=$(docker port "$CONTAINER" 80/tcp | head -n 1 | sed 's/.*://')
  export PORT
  for _ in $(seq 50); do
    curl -sf -o /dev/null "http://127.0.0.1:$PORT/index.html" && return 0
    sleep 0.1
  done
  return 1
}

teardown_file() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}

cache_control() {
  curl -s -D - -o /dev/null "http://127.0.0.1:$PORT$1" | tr -d '\r' | sed -n 's/^cache-control: //Ip'
}

@test "the root, a page route and the manifest are never cached" {
  local path value
  for path in / /today /manifest.webmanifest; do
    value=$(cache_control "$path")
    [[ "$value" == *no-store* ]] || {
      echo "$path answered Cache-Control: '$value'"
      return 1
    }
  done
}

@test "a built asset is cached for a year" {
  [[ "$(cache_control /assets/index-abc123.js)" == *immutable* ]]
}
