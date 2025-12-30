#!/usr/bin/env bash
# SSL Certificate management script for Traefik environments
# Usage: ./ssl-manager.sh [generate|validate|info] [dev|test|prod|all]

set -e

# Default values
ACTION="${1:-info}"
ENVIRONMENT="${2:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$(dirname "$SCRIPT_DIR")/certs"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get domain for environment
get_domain() {
    local env="$1"
    case "$env" in
        dev)
            echo "*.docker.localhost"
            ;;
        test)
            echo "*.test.localhost"
            ;;
        prod)
            echo "*.yourdomain.local"
            ;;
        *)
            print_error "Unknown environment: $env"
            exit 1
            ;;
    esac
}

# Generate certificate for environment
generate_cert() {
    local env="$1"
    local cert_file="$CERTS_DIR/${env}.crt"
    local key_file="$CERTS_DIR/${env}.key"

    print_info "Generating SSL certificate for $env environment"

    # Create certs directory if it doesn't exist
    mkdir -p "$CERTS_DIR"

    # Check if mkcert is available
    if command -v mkcert >/dev/null 2>&1; then
        print_info "Using mkcert for trusted local development certificates"

        # Define domains for each environment
        case "$env" in
            dev)
                local domains=("docker.localhost" "*.docker.localhost" "api.docker.localhost" "app.docker.localhost" "chat.docker.localhost" "dashboard.docker.localhost")
                ;;
            test)
                local domains=("test.localhost" "*.test.localhost" "api.test.localhost" "app.test.localhost" "chat.test.localhost" "dashboard.test.localhost")
                ;;
            prod)
                local domains=("yourdomain.local" "*.yourdomain.local" "api.yourdomain.local" "app.yourdomain.local" "chat.yourdomain.local" "dashboard.yourdomain.local")
                ;;
        esac

        # Check if mkcert local CA is installed
        if ! mkcert -check-ca >/dev/null 2>&1; then
            print_warning "mkcert local CA not installed. Installing..."
            mkcert -install
        fi

        # Generate certificate with mkcert
        cd "$CERTS_DIR"
        mkcert -key-file "${env}.key" -cert-file "${env}.crt" "${domains[@]}"

        print_success "mkcert certificate generated for $env environment"
        print_info "This certificate will be trusted by browsers without warnings"
    else
        print_warning "mkcert not found, falling back to OpenSSL self-signed certificate"
        print_info "Install mkcert for browser-trusted certificates: brew install mkcert"

        local domain=$(get_domain "$env")

        # Generate certificate with OpenSSL (legacy fallback)
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$key_file" \
            -out "$cert_file" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$domain" \
            -extensions v3_req \
            -config <(cat <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C=US
ST=State
L=City
O=Organization
CN=$domain

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $domain
DNS.2 = api.${domain#*.}
DNS.3 = app.${domain#*.}
DNS.4 = chat.${domain#*.}
DNS.5 = dashboard.${domain#*.}
EOF
        )

        print_success "OpenSSL certificate generated for $env environment"
        print_warning "This certificate may show security warnings in browsers"
    fi

    # Set appropriate permissions
    chmod 600 "$key_file"
    chmod 644 "$cert_file"

    print_info "Certificate: $cert_file"
    print_info "Private key: $key_file"
}

# Validate certificate
validate_cert() {
    local env="$1"
    local cert_file="$CERTS_DIR/${env}.crt"
    local key_file="$CERTS_DIR/${env}.key"

    print_info "Validating certificate for $env environment"

    if [ ! -f "$cert_file" ]; then
        print_error "Certificate file not found: $cert_file"
        return 1
    fi

    if [ ! -f "$key_file" ]; then
        print_error "Private key file not found: $key_file"
        return 1
    fi

    # Check if certificate is valid
    if openssl x509 -in "$cert_file" -noout -checkend 86400 >/dev/null 2>&1; then
        print_success "Certificate is valid for $env environment"

        # Show certificate details
        local expiry=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
        local subject=$(openssl x509 -in "$cert_file" -noout -subject | cut -d= -f2-)
        local sans=$(openssl x509 -in "$cert_file" -noout -text | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/^ *//')

        print_info "Subject: $subject"
        print_info "Expires: $expiry"
        print_info "SANs: $sans"

        # Check if private key matches certificate
        local cert_modulus=$(openssl x509 -noout -modulus -in "$cert_file" | openssl md5)
        local key_modulus=$(openssl rsa -noout -modulus -in "$key_file" 2>/dev/null | openssl md5)

        if [ "$cert_modulus" = "$key_modulus" ]; then
            print_success "Private key matches certificate"
        else
            print_error "Private key does not match certificate!"
            return 1
        fi
    else
        print_error "Certificate is expired or invalid for $env environment"
        return 1
    fi
}

# Show certificate info
show_cert_info() {
    local env="$1"
    local cert_file="$CERTS_DIR/${env}.crt"
    local key_file="$CERTS_DIR/${env}.key"

    print_info "Certificate information for $env environment"

    if [ ! -f "$cert_file" ]; then
        print_warning "Certificate file not found: $cert_file"
        return 0
    fi

    echo ""
    echo "Certificate file: $cert_file"
    echo "Private key file: $key_file"
    echo ""

    # Show certificate details
    openssl x509 -in "$cert_file" -noout -text | head -20
    echo ""

    # Show validity
    local not_before=$(openssl x509 -in "$cert_file" -noout -startdate | cut -d= -f2)
    local not_after=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)

    echo "Valid from: $not_before"
    echo "Valid until: $not_after"
    echo ""

    # Check if expiring soon (within 30 days)
    if openssl x509 -in "$cert_file" -noout -checkend 2592000 >/dev/null 2>&1; then
        print_success "Certificate is valid and not expiring soon"
    else
        print_warning "Certificate expires within 30 days!"
    fi
}

# Process environment list
process_environments() {
    local action="$1"
    local envs

    if [ "$ENVIRONMENT" = "all" ]; then
        envs="dev test prod"
    else
        case "$ENVIRONMENT" in
            dev|test|prod)
                envs="$ENVIRONMENT"
                ;;
            *)
                print_error "Invalid environment: $ENVIRONMENT"
                print_info "Valid environments: dev, test, prod, all"
                exit 1
                ;;
        esac
    fi

    for env in $envs; do
        echo ""
        case "$action" in
            generate)
                generate_cert "$env"
                ;;
            validate)
                validate_cert "$env"
                ;;
            info)
                show_cert_info "$env"
                ;;
        esac
    done
}

# Show help
show_help() {
    echo "SSL Certificate Management Script for Traefik"
    echo ""
    echo "This script uses mkcert for browser-trusted certificates when available,"
    echo "falling back to OpenSSL self-signed certificates if mkcert is not found."
    echo ""
    echo "Usage: $0 [ACTION] [ENVIRONMENT]"
    echo ""
    echo "ACTION:"
    echo "  generate  - Generate new SSL certificate"
    echo "  validate  - Validate existing certificate"
    echo "  info      - Show certificate information (default)"
    echo "  help      - Show this help message"
    echo ""
    echo "ENVIRONMENT:"
    echo "  dev       - Development environment (*.docker.localhost)"
    echo "  test      - Testing environment (*.test.localhost)"
    echo "  prod      - Production environment (*.yourdomain.local)"
    echo "  all       - All environments (default)"
    echo ""
    echo "Examples:"
    echo "  $0 generate dev    # Generate certificate for development"
    echo "  $0 validate all    # Validate all certificates"
    echo "  $0 info prod       # Show production certificate info"
    echo ""
    echo "Prerequisites:"
    echo "  Install mkcert for browser-trusted certificates:"
    echo "    macOS: brew install mkcert"
    echo "    Linux: see https://github.com/FiloSottile/mkcert#installation"
    echo "  Run 'mkcert -install' once to trust the local CA"
}

# Main execution
main() {
    case "$ACTION" in
        generate|validate|info)
            process_environments "$ACTION"
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Invalid action: $ACTION"
            print_info "Valid actions: generate, validate, info, help"
            exit 1
            ;;
    esac
}

# Run main function
main
