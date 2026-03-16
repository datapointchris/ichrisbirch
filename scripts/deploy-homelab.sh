#!/usr/bin/env bash
#
# Blue/green deployment script for ichrisbirch
#
# Deploys the opposite color from what's currently live, verifies health and
# smoke tests, then atomically switches Traefik routing. If anything fails
# before the switch, the live containers are never touched.
#
# Flow:
#   1. Acquire deploy lock (prevents concurrent deploys)
#   2. Pull latest code + decrypt secrets
#   3. Determine which color to deploy (opposite of live)
#   4. Ensure infrastructure (Traefik, PostgreSQL, Redis) is running
#   5. Build new images and start new color containers
#   6. Wait for health checks + run smoke tests
#   7. Run database migrations
#   8. Switch Traefik routing to new color
#   9. Grace period, then tear down old color
#
# Usage:
#   ./scripts/deploy-homelab.sh

set -euo pipefail

INSTALL_DIR="/srv/ichrisbirch"
LOG_DIR="${INSTALL_DIR}/logs"
LOG_FILE="${LOG_DIR}/deploy.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LOCK_FILE="/var/lock/ichrisbirch-deploy.lock"
STATE_DIR="/var/lib/ichrisbirch"
STATE_FILE="${STATE_DIR}/bluegreen-state"
COMPOSE_INFRA="docker compose --project-name icb-infra -f docker-compose.infra.yml"
GRACE_PERIOD=30

mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR"

# Source structured logging library
# shellcheck source=bash-lib/logging.sh
source "${SCRIPT_DIR}/bash-lib/logging.sh"

# Track deployment state for cleanup
DEPLOY_STARTED=false
DEPLOY_SUCCESS=false
CURRENT_SHA=""
NEW_SHA=""
DEPLOY_START_TIME=""
FAILURE_STEP=""
FAILURE_OUTPUT=""
LIVE_COLOR=""
DEPLOY_COLOR=""

compose_app() {
    local color="$1"
    shift
    DEPLOY_COLOR="$color" docker compose --project-name "icb-${color}" -f docker-compose.app.yml "$@"
}

cleanup() {
    local exit_code=$?

    # Always release the lock
    rmdir "$LOCK_FILE" 2>/dev/null || true

    if [[ "$DEPLOY_STARTED" == "true" && "$DEPLOY_SUCCESS" != "true" ]]; then
        local commit_msg
        commit_msg=$(cd "$INSTALL_DIR" && git log -1 --pretty=format:'%h - %s' 2>/dev/null || echo "unknown")

        log_error "deployment_failed" \
            "exit_code" "$exit_code" \
            "step" "${FAILURE_STEP:-unknown}" \
            "current_sha" "${CURRENT_SHA:-unknown}" \
            "target_sha" "${NEW_SHA:-unknown}" \
            "live_color" "${LIVE_COLOR:-unknown}" \
            "deploy_color" "${DEPLOY_COLOR:-unknown}" | tee -a "$LOG_FILE"

        # Clean up failed deploy containers (live containers stay untouched)
        if [[ -n "$DEPLOY_COLOR" ]]; then
            log_info "cleaning_up_failed_deploy" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
            compose_app "$DEPLOY_COLOR" down 2>/dev/null || true
        fi


        local message="*Commit:* \`${NEW_SHA:0:7}\`"
        message+="\n*Step Failed:* ${FAILURE_STEP:-unknown}"
        message+="\n*Exit Code:* $exit_code"
        message+="\n*Live Color:* ${LIVE_COLOR:-unknown} (still serving)"
        message+="\n\n*Commit:* $commit_msg"

        local context=""
        if [[ -n "$FAILURE_OUTPUT" ]]; then
            local truncated_output="${FAILURE_OUTPUT: -500}"
            context="*Error Output:*\n\`\`\`${truncated_output}\`\`\`"
        fi
        context+="\n\n*Logs:* \`/srv/ichrisbirch/logs/\`"

        notify_slack "failure" "$message" "$context"
    fi
}
trap cleanup EXIT

acquire_lock() {
    if ! mkdir "$LOCK_FILE" 2>/dev/null; then
        log_warn "deploy_already_running" "lock" "$LOCK_FILE" | tee -a "$LOG_FILE"
        # Not a failure — another deploy is handling it
        DEPLOY_STARTED=false
        exit 0
    fi
    log_info "lock_acquired" | tee -a "$LOG_FILE"
}

check_prerequisites() {
    FAILURE_STEP="prerequisites"
    if [[ ! -d "$INSTALL_DIR" ]]; then
        FAILURE_OUTPUT="Install directory not found: $INSTALL_DIR"
        log_error "prerequisite_failed" "reason" "install_dir_not_found" "path" "$INSTALL_DIR" | tee -a "$LOG_FILE"
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        FAILURE_OUTPUT="Docker command not found"
        log_error "prerequisite_failed" "reason" "docker_not_found" | tee -a "$LOG_FILE"
        exit 1
    fi

    if ! command -v jq &>/dev/null; then
        FAILURE_OUTPUT="jq not found — needed for smoke test validation"
        log_error "prerequisite_failed" "reason" "jq_not_found" | tee -a "$LOG_FILE"
        exit 1
    fi
}

decrypt_secrets() {
    FAILURE_STEP="decrypt_secrets"
    log_info "secrets_decrypt_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    if ! command -v sops &>/dev/null; then
        FAILURE_OUTPUT="sops not found - install from https://github.com/getsops/sops/releases"
        log_error "sops_not_found" | tee -a "$LOG_FILE"
        exit 1
    fi

    if [[ ! -f "secrets/secrets.prod.enc.env" ]]; then
        FAILURE_OUTPUT="Encrypted secrets file not found: secrets/secrets.prod.enc.env"
        log_error "secrets_file_missing" | tee -a "$LOG_FILE"
        exit 1
    fi

    if ! sops decrypt secrets/secrets.prod.enc.env > .env 2>&1; then
        FAILURE_OUTPUT="Failed to decrypt - check age key at ~/.config/sops/age/keys.txt"
        log_error "secrets_decrypt_failed" | tee -a "$LOG_FILE"
        exit 1
    fi

    log_info "secrets_decrypt_completed" | tee -a "$LOG_FILE"
}

pull_latest_code() {
    FAILURE_STEP="git_pull"
    log_info "git_fetch_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    if ! git fetch origin main 2>&1; then
        FAILURE_OUTPUT="Failed to fetch from origin"
        exit 1
    fi

    CURRENT_SHA=$(git rev-parse HEAD)
    NEW_SHA=$(git rev-parse origin/main)

    if [[ "$CURRENT_SHA" == "$NEW_SHA" ]]; then
        log_info "git_already_up_to_date" "sha" "${CURRENT_SHA:0:7}" | tee -a "$LOG_FILE"
    else
        log_info "git_pull_started" \
            "current_sha" "${CURRENT_SHA:0:7}" \
            "target_sha" "${NEW_SHA:0:7}" | tee -a "$LOG_FILE"
        if ! git pull origin main 2>&1; then
            FAILURE_OUTPUT="Failed to pull from origin/main"
            exit 1
        fi
        log_info "git_pull_completed" "sha" "${NEW_SHA:0:7}" | tee -a "$LOG_FILE"
    fi
}

determine_colors() {
    FAILURE_STEP="determine_colors"

    if [[ -f "$STATE_FILE" ]]; then
        LIVE_COLOR=$(cat "$STATE_FILE")
    else
        # First deploy — no live color yet, default to deploying blue
        LIVE_COLOR=""
    fi

    if [[ "$LIVE_COLOR" == "blue" ]]; then
        DEPLOY_COLOR="green"
    else
        DEPLOY_COLOR="blue"
    fi

    log_info "colors_determined" \
        "live" "${LIVE_COLOR:-none}" \
        "deploy" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

ensure_infra_running() {
    FAILURE_STEP="infra_startup"
    log_info "infra_check_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Start infra if not already running (idempotent)
    if ! $COMPOSE_INFRA up -d 2>&1 | tee -a "$LOG_FILE"; then
        FAILURE_OUTPUT="Failed to start infrastructure services"
        log_error "infra_startup_failed" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Wait for postgres and redis to be healthy
    local max_wait=60
    local interval=5
    local waited=0

    while [[ $waited -lt $max_wait ]]; do
        local pg_health redis_health
        pg_health=$(docker inspect --format='{{.State.Health.Status}}' icb-infra-postgres 2>/dev/null || echo "missing")
        redis_health=$(docker inspect --format='{{.State.Health.Status}}' icb-infra-redis 2>/dev/null || echo "missing")

        if [[ "$pg_health" == "healthy" && "$redis_health" == "healthy" ]]; then
            log_info "infra_healthy" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
            return 0
        fi

        sleep $interval
        waited=$((waited + interval))
    done

    FAILURE_OUTPUT="Infrastructure not healthy after ${max_wait}s. postgres=${pg_health}, redis=${redis_health}"
    log_error "infra_not_healthy" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
    exit 1
}

build_new_images() {
    FAILURE_STEP="build"
    log_info "build_started" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Remove any stale images from a previous failed build to avoid
    # "image already exists" errors with BuildKit shared image builds
    docker image rm "ichrisbirch:${DEPLOY_COLOR}" 2>/dev/null || true
    docker image rm "ichrisbirch-vue:${DEPLOY_COLOR}" 2>/dev/null || true

    local build_log="${LOG_DIR}/build-$(date +%Y%m%d-%H%M%S).log"

    if ! compose_app "$DEPLOY_COLOR" build 2>&1 | tee "$build_log"; then
        FAILURE_OUTPUT=$(tail -30 "$build_log")
        log_error "build_failed" "color" "$DEPLOY_COLOR" "log" "$build_log" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Keep only last 5 build logs
    # shellcheck disable=SC2012
    ls -t "${LOG_DIR}"/build-*.log 2>/dev/null | tail -n +6 | xargs -r rm -f

    log_info "build_completed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

start_new_containers() {
    FAILURE_STEP="start_containers"
    log_info "containers_starting" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    if ! compose_app "$DEPLOY_COLOR" up -d 2>&1 | tee -a "$LOG_FILE"; then
        FAILURE_OUTPUT="Failed to start ${DEPLOY_COLOR} containers"
        log_error "containers_start_failed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
        exit 1
    fi

    log_info "containers_started" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

wait_for_healthy() {
    FAILURE_STEP="health_check"
    local max_wait=90
    local interval=5
    local waited=0
    local services="icb-${DEPLOY_COLOR}-api icb-${DEPLOY_COLOR}-app icb-${DEPLOY_COLOR}-vue"

    log_info "waiting_for_healthy" "color" "$DEPLOY_COLOR" "max_wait" "$max_wait" | tee -a "$LOG_FILE"

    while [[ $waited -lt $max_wait ]]; do
        local all_healthy=true

        for service in $services; do
            local health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "missing")

            if [[ "$health" != "healthy" ]]; then
                all_healthy=false
                break
            fi
        done

        if [[ "$all_healthy" == "true" ]]; then
            log_info "containers_healthy" "color" "$DEPLOY_COLOR" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
            return 0
        fi

        sleep $interval
        waited=$((waited + interval))
    done

    # Log container statuses for debugging
    local container_statuses
    container_statuses=$(docker ps --format '{{.Names}}: {{.Status}}' | grep "icb-${DEPLOY_COLOR}" || echo "no containers")
    FAILURE_OUTPUT="Containers not healthy after ${max_wait}s. Status: $container_statuses"
    log_error "containers_not_healthy" "color" "$DEPLOY_COLOR" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
    exit 1
}

run_migrations() {
    FAILURE_STEP="migrations"
    log_info "migrations_started" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    local migration_output
    if migration_output=$(docker exec -w /app/ichrisbirch "icb-${DEPLOY_COLOR}-api" alembic upgrade head 2>&1); then
        log_info "migrations_completed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
    else
        FAILURE_OUTPUT="$migration_output"
        log_error "migrations_failed" "color" "$DEPLOY_COLOR" "output" "$migration_output" | tee -a "$LOG_FILE"
        exit 1
    fi
}

run_smoke_tests() {
    FAILURE_STEP="smoke_tests"
    log_info "smoke_tests_started" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"

    # Run the full 32-endpoint smoke test suite via the API's built-in endpoint
    local smoke_output
    if ! smoke_output=$(docker exec "icb-${DEPLOY_COLOR}-api" curl -sf \
        -X POST http://localhost:8000/admin/smoke-tests/ \
        -H "Remote-User: admin@ichrisbirch.com" \
        -H "Remote-Email: admin@ichrisbirch.com" 2>&1); then
        FAILURE_OUTPUT="Failed to reach smoke test endpoint: $smoke_output"
        log_error "smoke_tests_unreachable" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Verify all critical endpoints passed
    if ! echo "$smoke_output" | jq -e '.all_critical_passed == true' >/dev/null 2>&1; then
        local failed_endpoints
        failed_endpoints=$(echo "$smoke_output" | jq -r '.results[] | select(.passed == false) | "\(.path) (\(.status_code // .error))"' 2>/dev/null || echo "unknown")
        FAILURE_OUTPUT="Critical smoke tests failed: $failed_endpoints"
        log_error "smoke_tests_failed" "color" "$DEPLOY_COLOR" "failed" "$failed_endpoints" | tee -a "$LOG_FILE"
        exit 1
    fi

    local passed total
    passed=$(echo "$smoke_output" | jq -r '.passed' 2>/dev/null || echo "?")
    total=$(echo "$smoke_output" | jq -r '.total' 2>/dev/null || echo "?")
    log_info "smoke_tests_passed" "color" "$DEPLOY_COLOR" "passed" "$passed" "total" "$total" | tee -a "$LOG_FILE"

    # Verify Vue SPA serves correctly
    if ! docker exec "icb-${DEPLOY_COLOR}-vue" wget -qO- http://127.0.0.1:80/ >/dev/null 2>&1; then
        FAILURE_OUTPUT="Vue container not serving SPA"
        log_error "vue_smoke_failed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Verify Flask health
    if ! docker exec "icb-${DEPLOY_COLOR}-app" curl -sf http://localhost:5000/health >/dev/null 2>&1; then
        FAILURE_OUTPUT="Flask container health check failed"
        log_error "flask_smoke_failed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
        exit 1
    fi

    log_info "all_smoke_tests_passed" "color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

switch_traffic() {
    FAILURE_STEP="switch_traffic"
    log_info "traffic_switch_started" \
        "from" "${LIVE_COLOR:-none}" \
        "to" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Generate routing.yml pointing to the new color
    # The routing template uses "blue" as default; swap to the deploy color
    local routing_template="${INSTALL_DIR}/deploy-containers/traefik/dynamic/prod/routing.yml"
    local routing_tmp="${routing_template}.tmp"

    # Replace color in service URLs and the "Active color" comment
    if [[ "$DEPLOY_COLOR" == "green" ]]; then
        sed 's/icb-blue/icb-green/g; s/Active color: blue/Active color: green/' \
            "$routing_template" > "$routing_tmp"
    else
        sed 's/icb-green/icb-blue/g; s/Active color: green/Active color: blue/' \
            "$routing_template" > "$routing_tmp"
    fi

    # Atomic swap — Traefik watches the file and reloads within 1-2 seconds
    mv "$routing_tmp" "$routing_template"

    log_info "traffic_switched" "active_color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

update_state() {
    echo "$DEPLOY_COLOR" > "$STATE_FILE"
    log_info "state_updated" "active_color" "$DEPLOY_COLOR" | tee -a "$LOG_FILE"
}

stop_old_containers() {
    if [[ -z "$LIVE_COLOR" ]]; then
        log_info "no_old_containers" "reason" "first_deploy" | tee -a "$LOG_FILE"
        return 0
    fi

    log_info "grace_period_started" "seconds" "$GRACE_PERIOD" "old_color" "$LIVE_COLOR" | tee -a "$LOG_FILE"
    sleep "$GRACE_PERIOD"

    log_info "stopping_old_containers" "color" "$LIVE_COLOR" | tee -a "$LOG_FILE"
    compose_app "$LIVE_COLOR" down 2>&1 | tee -a "$LOG_FILE" || true

    log_info "old_containers_stopped" "color" "$LIVE_COLOR" | tee -a "$LOG_FILE"
}

cleanup_docker() {
    log_info "docker_cleanup_started" | tee -a "$LOG_FILE"
    docker builder prune --force 2>&1 | tail -1 | tee -a "$LOG_FILE" || true
    docker image prune -f 2>&1 | tail -1 | tee -a "$LOG_FILE" || true
    sudo fstrim -v / 2>&1 | tee -a "$LOG_FILE" || true
    log_info "docker_cleanup_completed" | tee -a "$LOG_FILE"
}

main() {
    DEPLOY_STARTED=true
    DEPLOY_START_TIME=$(date +%s)
    log_info "deployment_started" "install_dir" "$INSTALL_DIR" | tee -a "$LOG_FILE"

    acquire_lock
    check_prerequisites
    pull_latest_code
    decrypt_secrets

    # Source Slack webhook URL from decrypted .env
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        SLACK_WEBHOOK_URL=$(grep '^SLACK_WEBHOOK_URL=' "$INSTALL_DIR/.env" | cut -d= -f2- | tr -d '"')
        export SLACK_WEBHOOK_URL
    fi

    determine_colors
    ensure_infra_running
    build_new_images
    start_new_containers
    wait_for_healthy
    run_migrations
    run_smoke_tests

    # === POINT OF NO RETURN ===
    # Everything above verified successfully. Now switch traffic.
    switch_traffic
    update_state
    stop_old_containers
    cleanup_docker

    DEPLOY_SUCCESS=true

    local end_time duration_secs duration_str
    end_time=$(date +%s)
    duration_secs=$((end_time - DEPLOY_START_TIME))
    duration_str="$((duration_secs / 60))m $((duration_secs % 60))s"

    log_info "deployment_completed" \
        "sha" "${NEW_SHA:0:7}" \
        "color" "$DEPLOY_COLOR" \
        "duration_seconds" "$duration_secs" | tee -a "$LOG_FILE"

    local commit_msg
    commit_msg=$(cd "$INSTALL_DIR" && git log -1 --pretty=format:'%s' 2>/dev/null || echo "unknown")

    local message="*Commit:* \`${NEW_SHA:0:7}\` - $commit_msg"
    message+="\n*Duration:* ${duration_str}"
    message+="\n*Active Color:* ${DEPLOY_COLOR}"
    message+="\n*URL:* https://ichrisbirch.com"

    notify_slack "success" "$message"
}

main "$@"
