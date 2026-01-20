#!/usr/bin/env bash
#
# Homelab deployment script - called by webhook receiver after GitHub CI passes
#
# This script:
#   1. Pulls latest code from git
#   2. Runs Alembic database migrations
#   3. Rebuilds and restarts containers
#
# Usage:
#   ./scripts/deploy-homelab.sh
#
# The webhook receiver should call this script after receiving the deployment signal.

set -euo pipefail

INSTALL_DIR="/srv/ichrisbirch"
LOG_DIR="${INSTALL_DIR}/logs"
LOG_FILE="${LOG_DIR}/deploy.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "${BLUE}INFO${NC}" "$@"; }
log_success() { log "${GREEN}OK${NC}" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
    fi
}
trap cleanup EXIT

check_prerequisites() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Installation directory not found: $INSTALL_DIR"
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        log_error "Docker not found"
        exit 1
    fi
}

pull_latest_code() {
    log_info "Pulling latest code..."
    cd "$INSTALL_DIR"

    # Fetch and show what's coming
    git fetch origin main

    local current_sha new_sha
    current_sha=$(git rev-parse HEAD)
    new_sha=$(git rev-parse origin/main)

    if [[ "$current_sha" == "$new_sha" ]]; then
        log_info "Already up to date at ${current_sha:0:7}"
    else
        log_info "Updating ${current_sha:0:7} -> ${new_sha:0:7}"
        git pull origin main
    fi

    log_success "Code updated"
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$INSTALL_DIR"

    # Check if postgres is running
    if ! docker ps --format '{{.Names}}' | grep -q 'icb-prod-postgres'; then
        log_warn "Postgres container not running, starting services first..."
        ./cli/ichrisbirch prod start
        sleep 10
    fi

    # Run migrations via the api container (has alembic installed)
    # alembic.ini is in /app/ichrisbirch/
    if docker exec -w /app/ichrisbirch icb-prod-api alembic upgrade head; then
        log_success "Migrations complete"
    else
        log_error "Migration failed"
        exit 1
    fi
}

restart_services() {
    log_info "Restarting services..."
    cd "$INSTALL_DIR"

    # Rebuild images to pick up code changes and restart
    ./cli/ichrisbirch prod rebuild

    log_success "Services restarted"
}

verify_deployment() {
    log_info "Verifying deployment..."
    cd "$INSTALL_DIR"

    # Wait for services to be ready
    sleep 5

    # Check health
    if ./cli/ichrisbirch prod health; then
        log_success "Health check passed"
    else
        log_warn "Health check reported issues - check logs"
    fi
}

main() {
    log_info "=========================================="
    log_info "Starting homelab deployment"
    log_info "=========================================="

    check_prerequisites
    pull_latest_code
    run_migrations
    restart_services
    verify_deployment

    log_success "=========================================="
    log_success "Deployment complete"
    log_success "=========================================="
}

main "$@"
