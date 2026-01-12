#!/usr/bin/env bash
#
# Bootstrap script for deploying ichrisbirch on a fresh LXC container
# with Docker and Cloudflare Tunnel.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/datapointchris/ichrisbirch/master/scripts/bootstrap-homelab.sh | bash
#
# Or clone first and run:
#   ./scripts/bootstrap-homelab.sh
#
# Prerequisites:
#   - LXC container with Docker-compatible settings (see docs/homelab-deployment.md)
#   - AWS credentials available (will be configured during setup)
#   - Cloudflare account with tunnel token ready

set -euo pipefail

INSTALL_DIR="/srv/ichrisbirch"
REPO_URL="https://github.com/datapointchris/ichrisbirch.git"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_prerequisites() {
    log_info "Installing prerequisites..."
    apt update
    apt install -y curl git unzip
    log_success "Prerequisites installed"
}

install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker already installed: $(docker --version)"
        return
    fi

    log_info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh

    systemctl enable docker
    systemctl start docker
    log_success "Docker installed"
}

install_aws_cli() {
    if command -v aws &> /dev/null; then
        log_success "AWS CLI already installed: $(aws --version)"
        return
    fi

    log_info "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
    cd /tmp
    unzip -q awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
    log_success "AWS CLI installed"
}

install_cloudflared() {
    if command -v cloudflared &> /dev/null; then
        log_success "cloudflared already installed: $(cloudflared --version)"
        return
    fi

    log_info "Installing cloudflared..."
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/cloudflared.list
    apt update
    apt install -y cloudflared
    log_success "cloudflared installed"
}

clone_repository() {
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Repository exists, pulling latest..."
        cd "$INSTALL_DIR"
        git pull
    else
        log_info "Cloning repository to $INSTALL_DIR..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    log_success "Repository ready at $INSTALL_DIR"
}

install_cli() {
    log_info "Installing ichrisbirch CLI..."
    ln -sf "$INSTALL_DIR/cli/ichrisbirch" /usr/local/bin/ichrisbirch
    log_success "CLI installed: ichrisbirch"
}

setup_aws_credentials() {
    if [[ -f ~/.aws/credentials ]]; then
        log_success "AWS credentials already configured"
        return
    fi

    log_warn "AWS credentials not found"
    echo ""
    echo "You need to configure AWS credentials for SSM parameter access."
    echo "Options:"
    echo "  1. Run 'aws configure' manually"
    echo "  2. Copy ~/.aws from another machine"
    echo ""
    read -p "Configure AWS now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        aws configure
    else
        log_warn "Skipping AWS configuration - you'll need to do this before running prod commands"
    fi
}

create_docker_network() {
    if docker network inspect proxy >/dev/null 2>&1; then
        log_success "Docker proxy network exists"
    else
        log_info "Creating Docker proxy network..."
        docker network create proxy
        log_success "Created proxy network"
    fi
}

setup_cloudflare_tunnel() {
    if systemctl is-active --quiet cloudflared 2>/dev/null; then
        log_success "Cloudflare tunnel already running"
        return
    fi

    echo ""
    log_warn "Cloudflare tunnel not configured"
    echo ""
    echo "To set up the tunnel:"
    echo "  1. Go to https://dash.cloudflare.com -> Zero Trust -> Networks -> Tunnels"
    echo "  2. Create a tunnel named 'ichrisbirch-homelab'"
    echo "  3. Copy the tunnel token"
    echo ""
    read -rp "Enter tunnel token (or press Enter to skip): " tunnel_token

    if [[ -n "$tunnel_token" ]]; then
        log_info "Installing cloudflared service..."
        cloudflared service install "$tunnel_token"
        systemctl enable cloudflared
        systemctl start cloudflared
        log_success "Cloudflare tunnel configured and running"
    else
        log_warn "Skipping tunnel configuration - run 'sudo cloudflared service install <token>' later"
    fi
}

initialize_database() {
    echo ""
    log_info "Database initialization options:"
    echo "  1. Fresh database (run migrations)"
    echo "  2. Restore from backup file"
    echo "  3. Skip (database already set up)"
    echo ""
    read -p "Choose option [1/2/3]: " -n 1 -r db_option
    echo

    case $db_option in
        1)
            log_info "Will initialize fresh database after containers start"
            echo "fresh" > /tmp/ichrisbirch_db_init
            ;;
        2)
            read -rp "Enter backup file path: " backup_path
            if [[ -f "$backup_path" ]]; then
                echo "$backup_path" > /tmp/ichrisbirch_db_restore
                log_info "Will restore from $backup_path after containers start"
            else
                log_error "Backup file not found: $backup_path"
            fi
            ;;
        3)
            log_info "Skipping database initialization"
            ;;
        *)
            log_warn "Invalid option, skipping database initialization"
            ;;
    esac
}

start_services() {
    log_info "Starting production services..."
    cd "$INSTALL_DIR"

    if ! command -v ichrisbirch &> /dev/null; then
        log_error "CLI not in PATH, using direct path"
        "$INSTALL_DIR/cli/ichrisbirch" prod start
    else
        ichrisbirch prod start
    fi
}

post_start_database() {
    if [[ -f /tmp/ichrisbirch_db_init ]]; then
        log_info "Initializing fresh database..."
        # Wait for postgres to be ready
        sleep 10

        # Create role and database
        local pg_password
        pg_password=$(aws ssm get-parameter --region us-east-2 --name "/ichrisbirch/production/postgres/password" --with-decryption --query 'Parameter.Value' --output text)

        docker exec ichrisbirch-postgres psql -U postgres -c "CREATE ROLE ichrisbirch WITH LOGIN PASSWORD '$pg_password';"
        docker exec ichrisbirch-postgres psql -U postgres -c "ALTER ROLE ichrisbirch CREATEDB;"
        docker exec ichrisbirch-postgres psql -U postgres -c "ALTER DATABASE ichrisbirch OWNER TO ichrisbirch;"

        log_success "Database role created"
        rm /tmp/ichrisbirch_db_init

    elif [[ -f /tmp/ichrisbirch_db_restore ]]; then
        local backup_path
        backup_path=$(cat /tmp/ichrisbirch_db_restore)
        log_info "Restoring database from $backup_path..."

        # Wait for postgres
        sleep 10

        # Stop app services during restore
        docker stop ichrisbirch-api ichrisbirch-app ichrisbirch-chat ichrisbirch-scheduler 2>/dev/null || true

        # Create role if needed
        local pg_password
        pg_password=$(aws ssm get-parameter --region us-east-2 --name "/ichrisbirch/production/postgres/password" --with-decryption --query 'Parameter.Value' --output text)

        docker exec ichrisbirch-postgres psql -U postgres -c "CREATE ROLE ichrisbirch WITH LOGIN PASSWORD '$pg_password';" 2>/dev/null || true
        docker exec ichrisbirch-postgres psql -U postgres -c "ALTER ROLE ichrisbirch CREATEDB;" 2>/dev/null || true

        # Drop and recreate database
        docker exec ichrisbirch-postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ichrisbirch' AND pid <> pg_backend_pid();" 2>/dev/null || true
        docker exec ichrisbirch-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ichrisbirch;"
        docker exec ichrisbirch-postgres psql -U postgres -c "CREATE DATABASE ichrisbirch OWNER ichrisbirch;"

        # Restore
        docker exec -i ichrisbirch-postgres pg_restore -U ichrisbirch -d ichrisbirch --no-owner < "$backup_path" || true

        # Start services back up
        docker start ichrisbirch-api ichrisbirch-app ichrisbirch-chat ichrisbirch-scheduler

        log_success "Database restored"
        rm /tmp/ichrisbirch_db_restore
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Bootstrap Complete${NC}"
    echo "=========================================="
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Verify AWS credentials: aws sts get-caller-identity"
    echo "  2. Check services: ichrisbirch prod status"
    echo "  3. View logs: ichrisbirch prod logs"
    echo ""
    if ! systemctl is-active --quiet cloudflared 2>/dev/null; then
        echo -e "${YELLOW}Cloudflare tunnel not configured!${NC}"
        echo "  Run: sudo cloudflared service install <YOUR_TOKEN>"
        echo ""
    fi
    echo "Configure tunnel routes in Cloudflare dashboard:"
    echo "  - ichrisbirch.com -> http://localhost:80"
    echo "  - api.ichrisbirch.com -> http://localhost:80"
    echo "  - chat.ichrisbirch.com -> http://localhost:80"
    echo "  - www.ichrisbirch.com -> http://localhost:80"
    echo ""
    echo "Documentation: $INSTALL_DIR/docs/homelab-deployment.md"
    echo ""
}

main() {
    echo ""
    echo "=========================================="
    echo "ichrisbirch Homelab Bootstrap"
    echo "=========================================="
    echo ""

    check_root
    install_prerequisites
    install_docker
    install_aws_cli
    install_cloudflared
    clone_repository
    install_cli
    setup_aws_credentials
    create_docker_network
    setup_cloudflare_tunnel
    initialize_database
    start_services
    post_start_database
    print_summary
}

main "$@"
