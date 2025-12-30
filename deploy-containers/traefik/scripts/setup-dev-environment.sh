#!/usr/bin/env bash
# Setup script for Traefik development environment
# Generates SSL certificates and dashboard credentials

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAEFIK_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$TRAEFIK_DIR")")"
CERTS_DIR="$TRAEFIK_DIR/certs"
ENV_FILE="$PROJECT_ROOT/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_mkcert() {
    if ! command -v mkcert >/dev/null 2>&1; then
        print_error "mkcert is not installed"
        print_info "Install it with: brew install mkcert"
        exit 1
    fi

    if ! mkcert -check-ca >/dev/null 2>&1; then
        print_info "Installing mkcert local CA..."
        mkcert -install
    fi
}

generate_certificates() {
    print_info "Generating SSL certificates..."
    mkdir -p "$CERTS_DIR"

    local domains_dev=("docker.localhost" "*.docker.localhost" "api.docker.localhost" "app.docker.localhost" "chat.docker.localhost" "dashboard.docker.localhost")
    local domains_test=("test.localhost" "*.test.localhost" "api.test.localhost" "app.test.localhost" "chat.test.localhost" "dashboard.test.localhost")

    cd "$CERTS_DIR"

    print_info "Generating dev certificates..."
    mkcert -key-file "dev.key" -cert-file "dev.crt" "${domains_dev[@]}"
    chmod 600 "dev.key"
    chmod 644 "dev.crt"

    print_info "Generating test certificates..."
    mkcert -key-file "test.key" -cert-file "test.crt" "${domains_test[@]}"
    chmod 600 "test.key"
    chmod 644 "test.crt"

    print_success "SSL certificates generated in $CERTS_DIR"
}

generate_dashboard_credentials() {
    print_info "Generating Traefik dashboard credentials..."

    local username="dev"
    local password
    password=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)

    local hash
    hash=$(htpasswd -nbB "$username" "$password" | sed 's/\$/\$\$/g')

    if [ -f "$ENV_FILE" ]; then
        if grep -q "^TRAEFIK_DASHBOARD_AUTH=" "$ENV_FILE"; then
            sed -i "s|^TRAEFIK_DASHBOARD_AUTH=.*|TRAEFIK_DASHBOARD_AUTH=$hash|" "$ENV_FILE"
            print_info "Updated existing TRAEFIK_DASHBOARD_AUTH in .env"
        else
            {
                echo ""
                echo "# Traefik dashboard credentials (auto-generated)"
                echo "TRAEFIK_DASHBOARD_AUTH=$hash"
            } >> "$ENV_FILE"
            print_info "Added TRAEFIK_DASHBOARD_AUTH to .env"
        fi
    else
        print_warning ".env file not found at $ENV_FILE"
        print_info "Add the following to your .env file:"
        echo "TRAEFIK_DASHBOARD_AUTH=$hash"
    fi

    print_success "Dashboard credentials generated"
    print_info "Username: $username"
    print_info "Password: $password"
    print_warning "Save this password! It won't be shown again."
}

setup_acme_storage() {
    local acme_file="$TRAEFIK_DIR/acme.json"
    if [ ! -f "$acme_file" ]; then
        print_info "Creating acme.json for Let's Encrypt certificate storage..."
        touch "$acme_file"
        chmod 600 "$acme_file"
        print_success "Created $acme_file with correct permissions"
    else
        print_info "acme.json already exists"
    fi
}

show_help() {
    echo "Setup script for Traefik development environment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all          Run all setup steps (default)"
    echo "  certs        Generate SSL certificates only"
    echo "  credentials  Generate dashboard credentials only"
    echo "  acme         Create acme.json for Let's Encrypt"
    echo "  help         Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - mkcert (brew install mkcert)"
    echo "  - htpasswd (part of apache2-utils on Linux, pre-installed on macOS)"
}

main() {
    local command="${1:-all}"

    case "$command" in
        all)
            check_mkcert
            generate_certificates
            generate_dashboard_credentials
            setup_acme_storage
            echo ""
            print_success "Development environment setup complete!"
            print_info "Dashboard URL: https://dashboard.docker.localhost"
            ;;
        certs)
            check_mkcert
            generate_certificates
            ;;
        credentials)
            generate_dashboard_credentials
            ;;
        acme)
            setup_acme_storage
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
