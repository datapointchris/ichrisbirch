#!/usr/bin/env bash
#
# Homelab deployment script - called by webhook receiver after GitHub CI passes
#
# This script:
#   1. Pulls latest code from git
#   2. Runs Alembic database migrations
#   3. Rebuilds and restarts containers
#   4. Verifies deployment health
#   5. Sends Slack notification on success/failure
#
# Usage:
#   ./scripts/deploy-homelab.sh
#
# The webhook receiver should call this script after receiving the deployment signal.
# Logs are output as JSON for structured parsing.

set -euo pipefail

INSTALL_DIR="/srv/ichrisbirch"
LOG_DIR="${INSTALL_DIR}/logs"
LOG_FILE="${LOG_DIR}/deploy.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

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

cleanup() {
    local exit_code=$?
    if [[ "$DEPLOY_STARTED" == "true" && "$DEPLOY_SUCCESS" != "true" ]]; then
        local commit_msg
        commit_msg=$(cd "$INSTALL_DIR" && git log -1 --pretty=format:'%h - %s' 2>/dev/null || echo "unknown")

        log_error "deployment_failed" \
            "exit_code" "$exit_code" \
            "step" "${FAILURE_STEP:-unknown}" \
            "current_sha" "${CURRENT_SHA:-unknown}" \
            "target_sha" "${NEW_SHA:-unknown}" | tee -a "$LOG_FILE"

        # Build detailed failure message for Slack
        local message="*Commit:* \`${NEW_SHA:0:7}\`"
        message+="\n*Step Failed:* ${FAILURE_STEP:-unknown}"
        message+="\n*Exit Code:* $exit_code"
        message+="\n\n*Commit:* $commit_msg"

        local context=""
        if [[ -n "$FAILURE_OUTPUT" ]]; then
            # Truncate to last 500 chars to avoid Slack limits
            local truncated_output="${FAILURE_OUTPUT: -500}"
            context="*Error Output:*\n\`\`\`${truncated_output}\`\`\`"
        fi
        context+="\n\n*Logs:* \`/srv/ichrisbirch/logs/\`"

        notify_slack "failure" "$message" "$context"
    fi
}
trap cleanup EXIT

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
}

pull_latest_code() {
    FAILURE_STEP="git_pull"
    log_info "git_fetch_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Fetch and show what's coming
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

run_migrations() {
    FAILURE_STEP="migrations"
    log_info "migrations_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Check if postgres is running
    if ! docker ps --format '{{.Names}}' | grep -q 'icb-prod-postgres'; then
        log_warn "postgres_not_running" "action" "starting_services" | tee -a "$LOG_FILE"
        ./cli/ichrisbirch prod start
        sleep 10
    fi

    # Run migrations via the api container (has alembic installed)
    # alembic.ini is in /app/ichrisbirch/
    local migration_output
    if migration_output=$(docker exec -w /app/ichrisbirch icb-prod-api alembic upgrade head 2>&1); then
        log_info "migrations_completed" | tee -a "$LOG_FILE"
    else
        FAILURE_OUTPUT="$migration_output"
        log_error "migrations_failed" "output" "$migration_output" | tee -a "$LOG_FILE"
        exit 1
    fi
}

restart_services() {
    FAILURE_STEP="rebuild"
    log_info "services_restart_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Capture rebuild output to a log file for debugging
    local build_log="${LOG_DIR}/build-$(date +%Y%m%d-%H%M%S).log"

    # Rebuild images to pick up code changes and restart
    if ! ./cli/ichrisbirch prod rebuild 2>&1 | tee "$build_log"; then
        FAILURE_OUTPUT=$(tail -30 "$build_log")
        log_error "services_restart_failed" "step" "rebuild" "log" "$build_log" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Keep only last 5 build logs
    # shellcheck disable=SC2012
    ls -t "${LOG_DIR}"/build-*.log 2>/dev/null | tail -n +6 | xargs -r rm -f

    log_info "services_restart_completed" | tee -a "$LOG_FILE"
}

wait_for_containers_healthy() {
    local max_wait=90
    local interval=5
    local waited=0
    local services="icb-prod-api icb-prod-app icb-prod-traefik icb-prod-postgres icb-prod-redis"

    log_info "waiting_for_healthy" "max_wait" "$max_wait" | tee -a "$LOG_FILE"

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
            log_info "containers_healthy" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
            return 0
        fi

        sleep $interval
        waited=$((waited + interval))
    done

    log_warn "containers_not_healthy" "waited_seconds" "$waited" | tee -a "$LOG_FILE"
    return 1
}

verify_deployment() {
    FAILURE_STEP="health_check"
    log_info "health_check_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Wait for Docker healthchecks to pass
    if ! wait_for_containers_healthy; then
        # Log container statuses for debugging
        local container_statuses
        container_statuses=$(docker ps --format '{{.Names}}: {{.Status}}' | grep icb-prod || echo "no containers")
        FAILURE_OUTPUT="Containers not healthy after 90s. Status: $container_statuses"
        log_error "health_check_failed" "action" "deployment_blocked" "reason" "containers_not_healthy" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Run application-level health check
    local health_output
    if health_output=$(./cli/ichrisbirch prod health 2>&1); then
        log_info "health_check_passed" | tee -a "$LOG_FILE"
    else
        FAILURE_OUTPUT="$health_output"
        log_error "health_check_failed" "action" "deployment_blocked" | tee -a "$LOG_FILE"
        exit 1
    fi
}

main() {
    # Try to fetch Slack webhook URL from SSM (non-fatal if it fails)
    # shellcheck disable=SC2119
    fetch_slack_webhook_from_ssm || log_warn "slack_webhook_not_configured" | tee -a "$LOG_FILE"

    DEPLOY_STARTED=true
    DEPLOY_START_TIME=$(date +%s)
    log_info "deployment_started" "install_dir" "$INSTALL_DIR" | tee -a "$LOG_FILE"

    check_prerequisites
    pull_latest_code
    run_migrations
    restart_services
    verify_deployment

    DEPLOY_SUCCESS=true

    # Calculate duration
    local end_time duration_secs duration_str
    end_time=$(date +%s)
    duration_secs=$((end_time - DEPLOY_START_TIME))
    duration_str="$((duration_secs / 60))m $((duration_secs % 60))s"

    log_info "deployment_completed" \
        "sha" "${NEW_SHA:0:7}" \
        "duration_seconds" "$duration_secs" | tee -a "$LOG_FILE"

    # Get commit message for notification
    local commit_msg
    commit_msg=$(cd "$INSTALL_DIR" && git log -1 --pretty=format:'%s' 2>/dev/null || echo "unknown")

    # Build success message
    local message="*Commit:* \`${NEW_SHA:0:7}\` - $commit_msg"
    message+="\n*Duration:* ${duration_str}"
    message+="\n*URL:* https://ichrisbirch.com"

    notify_slack "success" "$message"
}

main "$@"
