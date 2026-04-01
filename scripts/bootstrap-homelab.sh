#!/usr/bin/env bash
#
# Bootstrap script for deploying ichrisbirch on a fresh LXC container
# with Docker and Cloudflare Tunnel.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/datapointchris/ichrisbirch/main/scripts/bootstrap-homelab.sh | bash
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
  if command -v docker &>/dev/null; then
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
  if command -v aws &>/dev/null; then
    log_success "AWS CLI already installed: $(aws --version)"
    return
  fi

  log_info "Installing AWS CLI (needed for S3 backups)..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  cd /tmp
  unzip -q awscliv2.zip
  ./aws/install
  rm -rf aws awscliv2.zip
  log_success "AWS CLI installed"
}

install_sops_age() {
  if command -v age &>/dev/null; then
    log_success "age already installed: $(age --version)"
  else
    log_info "Installing age..."
    apt-get install -y age
    log_success "age installed"
  fi

  if command -v sops &>/dev/null; then
    log_success "sops already installed: $(sops --version)"
  else
    log_info "Installing sops..."
    local sops_version="v3.9.4"
    curl -fsSL "https://github.com/getsops/sops/releases/download/${sops_version}/sops-${sops_version}.linux.amd64" -o /usr/local/bin/sops
    chmod +x /usr/local/bin/sops
    log_success "sops installed"
  fi
}

install_cloudflared() {
  if command -v cloudflared &>/dev/null; then
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
  ln -sf "$INSTALL_DIR/cli/icb" /usr/local/bin/icb
  log_success "CLI installed: icb"
}

setup_aws_credentials() {
  if [[ -f ~/.aws/credentials ]]; then
    log_success "AWS credentials already configured (needed for S3 backups)"
    return
  fi

  log_warn "AWS credentials not found"
  echo ""
  echo "AWS credentials are needed for S3 database backups."
  echo "Options:"
  echo "  1. Run 'aws configure' manually"
  echo "  2. Copy ~/.aws from another machine"
  echo ""
  read -p "Configure AWS now? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws configure
  else
    log_warn "Skipping AWS configuration - needed for S3 backups"
  fi
}

setup_age_key() {
  local key_dir="$HOME/.config/sops/age"
  if [[ -f "$key_dir/keys.txt" ]]; then
    log_success "age key already configured"
    return
  fi

  log_warn "age key not found at $key_dir/keys.txt"
  echo ""
  echo "The age private key is needed to decrypt production secrets."
  echo "Copy it from your laptop: scp ~/.config/sops/age/keys.txt $(hostname):$key_dir/keys.txt"
  echo ""
  read -p "Generate a new key instead? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$key_dir"
    age-keygen -o "$key_dir/keys.txt"
    log_success "age key generated - update .sops.yaml with the public key shown above"
  else
    mkdir -p "$key_dir"
    log_warn "Skipping age key setup - copy keys.txt before deploying"
  fi
}

decrypt_production_secrets() {
  cd "$INSTALL_DIR"
  if [[ -f ".env" ]]; then
    log_success ".env file already exists"
    return
  fi

  if [[ ! -f "secrets/secrets.prod.enc.env" ]]; then
    log_warn "No encrypted secrets file found - create .env manually"
    return
  fi

  if ! command -v sops &>/dev/null; then
    log_warn "sops not installed - cannot decrypt secrets"
    return
  fi

  log_info "Decrypting production secrets..."
  if sops decrypt secrets/secrets.prod.enc.env > .env 2>/dev/null; then
    log_success "Production secrets decrypted to .env"
  else
    log_error "Failed to decrypt secrets - check age key"
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
    echo "fresh" >/tmp/ichrisbirch_db_init
    ;;
  2)
    read -rp "Enter backup file path: " backup_path
    if [[ -f "$backup_path" ]]; then
      echo "$backup_path" >/tmp/ichrisbirch_db_restore
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

  if ! command -v icb &>/dev/null; then
    log_error "CLI not in PATH, using direct path"
    "$INSTALL_DIR/cli/icb" prod start
  else
    icb prod start
  fi
}

post_start_database() {
  if [[ -f /tmp/ichrisbirch_db_init ]]; then
    log_info "Initializing fresh database..."
    # Wait for postgres to be ready
    sleep 10

    # Create role and database
    local pg_password
    pg_password=$(grep '^POSTGRES_PASSWORD=' "$INSTALL_DIR/.env" | cut -d= -f2- | tr -d '"')

    docker exec icb-infra-postgres psql -U postgres -c "CREATE ROLE icb_app WITH LOGIN PASSWORD '$pg_password';"
    docker exec icb-infra-postgres psql -U postgres -c "ALTER ROLE icb_app CREATEDB;"
    docker exec icb-infra-postgres psql -U postgres -c "ALTER DATABASE ichrisbirch OWNER TO icb_app;"

    # Grant schema access and set default privileges for future objects
    docker exec icb-infra-postgres psql -U postgres -d ichrisbirch -c "
DO \$\$
DECLARE
    s TEXT;
BEGIN
    FOR s IN SELECT unnest(ARRAY['public','admin','apartments','box_packing','chat','habits'])
    LOOP
        EXECUTE format('GRANT ALL ON SCHEMA %I TO icb_app', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO icb_app', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON SEQUENCES TO icb_app', s);
    END LOOP;
END
\$\$;
"

    log_success "Database role created"
    rm /tmp/ichrisbirch_db_init

  elif [[ -f /tmp/ichrisbirch_db_restore ]]; then
    local backup_path
    backup_path=$(cat /tmp/ichrisbirch_db_restore)
    log_info "Restoring database from $backup_path..."

    # Wait for postgres
    sleep 10

    # Stop app services during restore
    docker stop icb-prod-api icb-prod-app icb-prod-chat icb-prod-scheduler 2>/dev/null || true

    # Create role if needed
    local pg_password
    pg_password=$(grep '^POSTGRES_PASSWORD=' "$INSTALL_DIR/.env" | cut -d= -f2- | tr -d '"')

    docker exec icb-infra-postgres psql -U postgres -c "CREATE ROLE icb_app WITH LOGIN PASSWORD '$pg_password';" 2>/dev/null || true
    docker exec icb-infra-postgres psql -U postgres -c "ALTER ROLE icb_app CREATEDB;" 2>/dev/null || true

    # Drop and recreate database
    docker exec icb-infra-postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ichrisbirch' AND pid <> pg_backend_pid();" 2>/dev/null || true
    docker exec icb-infra-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ichrisbirch;"
    docker exec icb-infra-postgres psql -U postgres -c "CREATE DATABASE ichrisbirch OWNER icb_app;"

    # Grant schema access and set default privileges for future objects
    docker exec icb-infra-postgres psql -U postgres -d ichrisbirch -c "
DO \$\$
DECLARE
    s TEXT;
BEGIN
    FOR s IN SELECT unnest(ARRAY['public','admin','apartments','box_packing','chat','habits'])
    LOOP
        EXECUTE format('GRANT ALL ON SCHEMA %I TO icb_app', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO icb_app', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON SEQUENCES TO icb_app', s);
    END LOOP;
END
\$\$;
"

    # Restore
    docker exec -i icb-infra-postgres pg_restore -U icb_app -d ichrisbirch --no-owner <"$backup_path" || true

    # Start services back up
    docker start icb-prod-api icb-prod-app icb-prod-chat icb-prod-scheduler

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
  echo "  1. Verify age key: sops decrypt secrets/secrets.prod.enc.env > /dev/null"
  echo "  2. Verify AWS credentials (for S3 backups): aws sts get-caller-identity"
  echo "  3. Check services: icb prod status"
  echo "  4. View logs: icb prod logs"
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
  install_sops_age
  install_cloudflared
  clone_repository
  install_cli
  setup_aws_credentials
  setup_age_key
  decrypt_production_secrets
  create_docker_network
  setup_cloudflare_tunnel
  initialize_database
  start_services
  post_start_database
  print_summary
}

main "$@"
