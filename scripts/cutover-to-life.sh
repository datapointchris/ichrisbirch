#!/usr/bin/env bash
#
# MIGRATION: moves the production host from the ichrisbirch layout to life's, once.
#
# deploy-homelab.sh runs this when it finds the old checkout and no new one, so
# the move rides the deploy that carries the rename. It stops the site, moves
# the checkout and the state directory, copies both volumes into life's, renames
# the database and its role, and checks every table's row count against the one
# read before the stop. It then hands over to the deploy script at its new path,
# which brings life up and switches traffic.
#
# The old volumes are only ever read. So until traffic switches, any failure,
# here or in the deploy, removes everything named life and starts the old stack
# again as it stood, and the next release tries again from the start.
#
# Usage:
#   cutover-to-life.sh              # move, then deploy
#   cutover-to-life.sh --roll-back  # what a deploy that failed before its switch runs

set -euo pipefail

OLD_DIR=/srv/ichrisbirch
NEW_DIR=/srv/life
OLD_STATE_DIR=/var/lib/ichrisbirch
NEW_STATE_DIR=/var/lib/life
LOCK_FILE=/var/lock/life-deploy.lock
# The lock the old layout's deploy takes, held too so no deploy of it runs under the move.
OLD_LOCK_FILE=/var/lock/ichrisbirch-deploy.lock
OLD_LOCK_HELD=false
OLD_DATABASE=ichrisbirch
NEW_DATABASE=life
OLD_ROLE=icb_app
NEW_ROLE=life
# Each old volume, then the one it is copied into.
VOLUMES=(icb-prod-postgres-data:life-prod-postgres-data icb-prod-redis-data:life-prod-redis-data)
OLD_INFRA=(icb-infra-postgres icb-infra-redis icb-infra-traefik)
NEW_INFRA="docker compose --project-name life-infra -f docker-compose.infra.yml"

# Every table's exact row count, one `schema.table|count` a line in name order.
ROW_COUNTS="SELECT format('SELECT %L || ''|'' || count(*) FROM %I.%I', schemaname || '.' || relname, schemaname, relname)
FROM pg_stat_user_tables ORDER BY schemaname, relname
\\gexec"

source "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/bash-lib/logging.sh"

# The checkout holds the log and this script, and it moves partway through.
checkout() {
  if [[ -d "$NEW_DIR/.git" ]]; then echo "$NEW_DIR"; else echo "$OLD_DIR"; fi
}

log_file() {
  echo "$(checkout)/logs/deploy.log"
}

say() {
  local level="$1"
  shift
  "log_${level}" "$@" | tee -a "$(log_file)"
}

STEP=""
HANDED_OVER=false

fail() {
  say error "cutover_refused" "step" "$STEP" "reason" "$1"
  exit 1
}

live_color() {
  local file
  for file in "$NEW_STATE_DIR/bluegreen-state" "$OLD_STATE_DIR/bluegreen-state"; do
    if [[ -f "$file" ]]; then
      cat "$file"
      return 0
    fi
  done
}

wait_healthy() {
  local container="$1" waited=0 health
  while ((waited < 120)); do
    health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo missing)
    [[ "$health" == healthy ]] && return 0
    sleep 1
    waited=$((waited + 1))
  done
  echo "$container is $health after ${waited}s" >&2
  return 1
}

row_counts() {
  docker exec -i "$1" psql -U postgres -d "$2" -At -v ON_ERROR_STOP=1 <<<"$ROW_COUNTS"
}

# Put the old stack back as it stood. Safe to run from any point, and twice.
roll_back() {
  say warn "cutover_roll_back_started"
  docker ps -aq --filter 'name=^life-' | xargs -r docker rm -f >/dev/null
  docker network rm life-infra_default >/dev/null 2>&1 || true
  local pair
  for pair in "${VOLUMES[@]}"; do
    docker volume rm "${pair#*:}" >/dev/null 2>&1 || true
  done
  if [[ -d "$NEW_DIR" && ! -e "$OLD_DIR" ]]; then
    sudo mv "$NEW_DIR" "$OLD_DIR"
  fi
  if [[ -d "$NEW_STATE_DIR" && ! -e "$OLD_STATE_DIR" ]]; then
    sudo mv "$NEW_STATE_DIR" "$OLD_STATE_DIR"
  fi
  local color
  color=$(live_color)
  local apps=("icb-${color}-api" "icb-${color}-vue" "icb-${color}-scheduler")
  docker update --restart=always "${OLD_INFRA[@]}" "${apps[@]}" >/dev/null
  docker start icb-infra-postgres icb-infra-redis >/dev/null
  wait_healthy icb-infra-postgres
  wait_healthy icb-infra-redis
  docker start icb-infra-traefik "${apps[@]}" >/dev/null
  wait_healthy "icb-${color}-api"
  wait_healthy "icb-${color}-vue"
  say info "cutover_roll_back_completed" "live_color" "$color"
}

on_exit() {
  local code=$?
  if [[ "$HANDED_OVER" != true && "$code" -ne 0 && -n "$STEP" && "$STEP" != preflight ]]; then
    # Its own process, so errexit stops the rollback at the first step that fails.
    local state
    if "$(checkout)/scripts/cutover-to-life.sh" --roll-back; then
      state="$(live_color) (serving again)"
    else
      say error "cutover_roll_back_failed" "step" "$STEP" "site" "down"
      state="none: the roll back failed and the site is DOWN"
    fi
    notify_slack "failure" "*Cutover to life failed at:* ${STEP}\n*Live color:* ${state}" \
      "*Logs:* \`$(log_file)\`"
  fi
  if [[ "$OLD_LOCK_HELD" == true ]]; then rmdir "$OLD_LOCK_FILE" 2>/dev/null || true; fi
  [[ "$HANDED_OVER" == true ]] || rmdir "$LOCK_FILE" 2>/dev/null || true
}

preflight() {
  STEP=preflight
  [[ -d "$OLD_DIR/.git" ]] || fail "$OLD_DIR holds no checkout"
  [[ ! -e "$NEW_DIR" && ! -e "$NEW_STATE_DIR" ]] || fail "$NEW_DIR or $NEW_STATE_DIR already exists"
  [[ -z "$(docker ps -aq --filter 'name=^life-')" ]] || fail "a container named life-* already exists"
  [[ -z "$(docker volume ls -q --filter 'name=^life-')" ]] || fail "a volume named life-* already exists"
  [[ -z "$(docker network ls -q --filter 'name=^life-')" ]] || fail "a network named life-* already exists"
  LIVE_COLOR=$(live_color)
  [[ "$LIVE_COLOR" == blue || "$LIVE_COLOR" == green ]] || fail "no live color in $OLD_STATE_DIR/bluegreen-state"
  [[ "$(docker inspect --format '{{.State.Running}}' icb-infra-postgres 2>/dev/null)" == true ]] || fail "icb-infra-postgres is not running"
}

decrypt_and_pull() {
  STEP=decrypt_and_pull
  cd "$OLD_DIR"
  sops decrypt secrets/secrets.prod.enc.env >.env
  POSTGRES_PASSWORD=$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2- | tr -d '"')
  SLACK_WEBHOOK_URL=$(grep '^SLACK_WEBHOOK_URL=' .env | cut -d= -f2- | tr -d '"')
  export SLACK_WEBHOOK_URL
  grep -qx "POSTGRES_DB=\"\?${NEW_DATABASE}\"\?" .env || fail ".env names a database other than $NEW_DATABASE"
  grep -qx "POSTGRES_USERNAME=\"\?${NEW_ROLE}\"\?" .env || fail ".env names a role other than $NEW_ROLE"
  # Pulled while the site still serves, so the stop waits on nothing the network decides.
  $NEW_INFRA pull --quiet
  DEPLOY_COLOR=blue docker compose --project-name life-blue -f docker-compose.app.yml pull --quiet
  say info "cutover_images_pulled"
}

stop_old_stack() {
  STEP=stop_old_stack
  SITE_STOPPED_AT=$(date +%s)
  say info "site_stopped" "live_color" "$LIVE_COLOR"
  local apps=("icb-${LIVE_COLOR}-scheduler" "icb-${LIVE_COLOR}-api" "icb-${LIVE_COLOR}-vue")
  # restart=no, so a reboot inside the window cannot bring them back on port 80.
  docker update --restart=no "${apps[@]}" "${OLD_INFRA[@]}" >/dev/null
  docker stop "${apps[@]}" >/dev/null
  # Read after the app stops and before Postgres does, so nothing writes between the two counts.
  row_counts icb-infra-postgres "$OLD_DATABASE" >"/tmp/cutover-rows-before.txt"
  docker stop -t 60 icb-infra-traefik icb-infra-redis icb-infra-postgres >/dev/null
  say info "old_stack_stopped" "tables" "$(wc -l <"/tmp/cutover-rows-before.txt")"
}

move_paths() {
  STEP=move_paths
  sudo mv "$OLD_DIR" "$NEW_DIR"
  sudo mv "$OLD_STATE_DIR" "$NEW_STATE_DIR"
  mv /tmp/cutover-rows-before.txt "$NEW_DIR/logs/cutover-rows-before.txt"
  cd "$NEW_DIR"
  say info "paths_moved" "install_dir" "$NEW_DIR" "state_dir" "$NEW_STATE_DIR"
}

copy_volumes() {
  STEP=copy_volumes
  # create makes the named volumes and the network, empty, with compose's labels.
  $NEW_INFRA create postgres redis >/dev/null
  local pair from to
  for pair in "${VOLUMES[@]}"; do
    from=${pair%%:*}
    to=${pair#*:}
    docker run --rm -v "${from}:/from:ro" -v "${to}:/to" --entrypoint sh postgres:16-alpine \
      -c '[ -z "$(ls -A /to)" ] || { echo "/to is not empty" >&2; exit 1; }; cp -a /from/. /to/'
    say info "volume_copied" "from" "$from" "to" "$to"
  done
}

rename_database() {
  STEP=rename_database
  $NEW_INFRA up -d --no-deps postgres >/dev/null
  wait_healthy life-infra-postgres
  docker exec -i life-infra-postgres psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q <<SQL
ALTER DATABASE ${OLD_DATABASE} RENAME TO ${NEW_DATABASE};
ALTER ROLE ${OLD_ROLE} RENAME TO ${NEW_ROLE};
SQL
  # A rename clears a password stored as MD5, which is salted with the role's
  # name, and keeps a SCRAM one. So only a cleared password is set again.
  local cleared
  cleared=$(docker exec life-infra-postgres psql -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
    -c "SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = '${NEW_ROLE}'")
  if [[ "$cleared" == t ]]; then
    docker exec -i life-infra-postgres psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q <<SQL
ALTER ROLE ${NEW_ROLE} PASSWORD \$cutover\$${POSTGRES_PASSWORD}\$cutover\$;
SQL
    say info "role_password_set_again" "reason" "rename_cleared_md5"
  fi
  docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" life-infra-postgres \
    psql -h 127.0.0.1 -U "$NEW_ROLE" -d "$NEW_DATABASE" -At -c 'SELECT 1' >/dev/null
  say info "database_renamed" "database" "$NEW_DATABASE" "role" "$NEW_ROLE"
}

compare_row_counts() {
  STEP=compare_row_counts
  local before="$NEW_DIR/logs/cutover-rows-before.txt" after="$NEW_DIR/logs/cutover-rows-after.txt"
  row_counts life-infra-postgres "$NEW_DATABASE" >"$after"
  if ! diff -u "$before" "$after" >&2; then
    fail "row counts differ between $before and $after"
  fi
  say info "row_counts_match" "tables" "$(wc -l <"$after")" "rows" "$(awk -F'|' '{n += $2} END {print n}' "$after")"
}

main() {
  if ! mkdir "$LOCK_FILE" 2>/dev/null; then
    echo "another deploy holds $LOCK_FILE" >&2
    exit 0
  fi
  trap on_exit EXIT
  STEP=preflight
  mkdir "$OLD_LOCK_FILE" 2>/dev/null || fail "a deploy of the old layout holds $OLD_LOCK_FILE"
  OLD_LOCK_HELD=true
  preflight
  say info "cutover_started" "from" "$OLD_DIR" "to" "$NEW_DIR"
  decrypt_and_pull
  stop_old_stack
  move_paths
  copy_volumes
  rename_database
  compare_row_counts
  say info "cutover_handed_to_deploy" "seconds_since_site_stopped" "$(($(date +%s) - SITE_STOPPED_AT))"
  HANDED_OVER=true
  # The old checkout is gone, so no deploy of the old layout can start from here on.
  rmdir "$OLD_LOCK_FILE"
  OLD_LOCK_HELD=false
  export CUTOVER_SITE_STOPPED_AT="$SITE_STOPPED_AT" CUTOVER_HOLDS_LOCK=1
  exec "$NEW_DIR/scripts/deploy-homelab.sh"
}

case "${1:-}" in
  --roll-back) roll_back ;;
  "") main ;;
  *)
    echo "usage: cutover-to-life.sh [--roll-back]" >&2
    exit 2
    ;;
esac
