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

cleanup() {
    local exit_code=$?
    if [[ "$DEPLOY_STARTED" == "true" && "$DEPLOY_SUCCESS" != "true" ]]; then
        log_error "deployment_failed" \
            "exit_code" "$exit_code" \
            "current_sha" "${CURRENT_SHA:-unknown}" \
            "target_sha" "${NEW_SHA:-unknown}" | tee -a "$LOG_FILE"
        notify_slack "failure" "ichrisbirch deployment FAILED (exit code: $exit_code)"
    fi
}
trap cleanup EXIT

check_prerequisites() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "prerequisite_failed" "reason" "install_dir_not_found" "path" "$INSTALL_DIR" | tee -a "$LOG_FILE"
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        log_error "prerequisite_failed" "reason" "docker_not_found" | tee -a "$LOG_FILE"
        exit 1
    fi
}

pull_latest_code() {
    log_info "git_fetch_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Fetch and show what's coming
    git fetch origin main

    CURRENT_SHA=$(git rev-parse HEAD)
    NEW_SHA=$(git rev-parse origin/main)

    if [[ "$CURRENT_SHA" == "$NEW_SHA" ]]; then
        log_info "git_already_up_to_date" "sha" "${CURRENT_SHA:0:7}" | tee -a "$LOG_FILE"
    else
        log_info "git_pull_started" \
            "current_sha" "${CURRENT_SHA:0:7}" \
            "target_sha" "${NEW_SHA:0:7}" | tee -a "$LOG_FILE"
        git pull origin main
        log_info "git_pull_completed" "sha" "${NEW_SHA:0:7}" | tee -a "$LOG_FILE"
    fi
}

run_migrations() {
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
        log_error "migrations_failed" "output" "$migration_output" | tee -a "$LOG_FILE"
        exit 1
    fi
}

restart_services() {
    log_info "services_restart_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Rebuild images to pick up code changes and restart
    if ! ./cli/ichrisbirch prod rebuild 2>&1; then
        log_error "services_restart_failed" "step" "rebuild" | tee -a "$LOG_FILE"
        exit 1
    fi

    log_info "services_restart_completed" | tee -a "$LOG_FILE"
}

verify_deployment() {
    log_info "health_check_started" | tee -a "$LOG_FILE"
    cd "$INSTALL_DIR"

    # Wait for services to be ready
    sleep 5

    # Check health - failures should BLOCK deployment
    if ./cli/ichrisbirch prod health 2>&1; then
        log_info "health_check_passed" | tee -a "$LOG_FILE"
    else
        log_error "health_check_failed" "action" "deployment_blocked" | tee -a "$LOG_FILE"
        exit 1
    fi
}

main() {
    # Try to fetch Slack webhook URL from SSM (non-fatal if it fails)
    # shellcheck disable=SC2119
    fetch_slack_webhook_from_ssm || log_warn "slack_webhook_not_configured" | tee -a "$LOG_FILE"

    DEPLOY_STARTED=true
    log_info "deployment_started" "install_dir" "$INSTALL_DIR" | tee -a "$LOG_FILE"

    check_prerequisites
    pull_latest_code
    run_migrations
    restart_services
    verify_deployment

    DEPLOY_SUCCESS=true
    log_info "deployment_completed" \
        "sha" "${NEW_SHA:0:7}" | tee -a "$LOG_FILE"

    # Get commit message for notification
    local commit_msg
    commit_msg=$(cd "$INSTALL_DIR" && git log -1 --pretty=format:'%s' 2>/dev/null || echo "unknown")
    notify_slack "success" "ichrisbirch deployed successfully: ${NEW_SHA:0:7} - $commit_msg"
}

main "$@"
