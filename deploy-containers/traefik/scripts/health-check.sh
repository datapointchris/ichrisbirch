#!/usr/bin/env bash
# Health check script for Traefik environments
# Usage: ./health-check.sh [dev|test|prod]

set -e

# Default values
ENVIRONMENT="${1:-dev}"

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
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Get URLs for environment
get_urls() {
    case "$ENVIRONMENT" in
        dev)
            API_URL="https://api.docker.localhost"
            APP_URL="https://app.docker.localhost"
            CHAT_URL="https://chat.docker.localhost"
            DASHBOARD_URL="https://dashboard.docker.localhost"
            API_HOST=""
            APP_HOST=""
            CHAT_HOST=""
            ;;
        test)
            API_URL="https://api.test.localhost:8443"
            APP_URL="https://app.test.localhost:8443"
            CHAT_URL="https://chat.test.localhost:8443"
            DASHBOARD_URL="https://dashboard.test.localhost:8443"
            API_HOST=""
            APP_HOST=""
            CHAT_HOST=""
            ;;
        prod)
            # Production: hit Traefik locally with Host headers
            # Cloudflare Tunnel routes external traffic, but we can test via localhost
            local domain="${DOMAIN:-ichrisbirch.com}"
            API_URL="http://localhost:80"
            APP_URL="http://localhost:80"
            CHAT_URL="http://localhost:80"
            DASHBOARD_URL=""
            API_HOST="api.${domain}"
            APP_HOST="${domain}"
            CHAT_HOST="chat.${domain}"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            print_info "Valid environments: dev, test, prod"
            exit 1
            ;;
    esac
}

# Check URL health
# Args: name, url, auth, expected_code, host_header
check_url() {
    local name="$1"
    local url="$2"
    local auth="$3"
    local expected_code="${4:-200}"
    local host_header="$5"

    if [ -n "$host_header" ]; then
        print_info "Checking $name at $url (Host: $host_header)"
    else
        print_info "Checking $name at $url"
    fi

    local status_code
    local curl_cmd="curl -k -s -o /dev/null -w '%{http_code}' --connect-timeout 10 --max-time 30"

    if [ -n "$host_header" ]; then
        curl_cmd="$curl_cmd -H 'Host: $host_header'"
    fi

    if [ -n "$auth" ]; then
        curl_cmd="$curl_cmd -u '$auth'"
    fi

    if status_code=$(eval "$curl_cmd '$url'" 2>/dev/null); then
        if [ "$status_code" = "$expected_code" ]; then
            print_success "$name: HTTP $status_code (OK)"
            return 0
        else
            print_warning "$name: HTTP $status_code (Expected $expected_code)"
            return 1
        fi
    else
        print_error "$name: Connection failed"
        return 1
    fi
}

# Check WebSocket functionality
check_websocket() {
    local name="$1"
    local url="$2"

    print_info "Checking WebSocket support for $name"

    local ws_url="${url}/_stcore/stream"
    local status_code

    if status_code=$(curl -k -s -o /dev/null -w '%{http_code}' \
        -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        -H "Sec-WebSocket-Version: 13" \
        --connect-timeout 10 --max-time 30 \
        "$ws_url" 2>/dev/null); then

        if [ "$status_code" = "426" ] || [ "$status_code" = "101" ]; then
            print_success "$name WebSocket: HTTP $status_code (WebSocket upgrade supported)"
            return 0
        else
            print_warning "$name WebSocket: HTTP $status_code (May not support WebSocket)"
            return 1
        fi
    else
        print_error "$name WebSocket: Connection failed"
        return 1
    fi
}

# Check DNS resolution
check_dns() {
    local domain="$1"

    print_info "Checking DNS resolution for $domain"

    if host "$domain" >/dev/null 2>&1; then
        local ip=$(host "$domain" | grep "has address" | awk '{print $4}' | head -1)
        if [ -n "$ip" ]; then
            print_success "DNS: $domain resolves to $ip"
            return 0
        fi
    fi

    # Check /etc/hosts
    if grep -q "$domain" /etc/hosts 2>/dev/null; then
        local ip=$(grep "$domain" /etc/hosts | awk '{print $1}' | head -1)
        print_success "DNS: $domain found in /etc/hosts ($ip)"
        return 0
    fi

    print_error "DNS: $domain does not resolve"
    return 1
}

# Check Docker containers
check_containers() {
    print_info "Checking Docker containers for $ENVIRONMENT environment"

    local containers=()

    case "$ENVIRONMENT" in
        dev)
            containers=(
                "ichrisbirch-traefik-dev"
                "ichrisbirch-api-dev"
                "ichrisbirch-app-dev"
                "ichrisbirch-chat-dev"
                "ichrisbirch-postgres-dev"
                "ichrisbirch-redis-dev"
                "ichrisbirch-scheduler-dev"
            )
            ;;
        test)
            containers=(
                "ichrisbirch-traefik-test"
                "ichrisbirch-api-testing"
                "ichrisbirch-app-testing"
                "ichrisbirch-chat-testing"
                "ichrisbirch-postgres-testing"
                "ichrisbirch-redis-testing"
                "ichrisbirch-scheduler-testing"
            )
            ;;
        prod)
            containers=(
                "ichrisbirch-traefik"
                "ichrisbirch-api"
                "ichrisbirch-app"
                "ichrisbirch-chat"
                "ichrisbirch-postgres"
                "ichrisbirch-redis"
                "ichrisbirch-scheduler"
            )
            ;;
    esac

    local all_running=true

    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^$container$"; then
            local status=$(docker ps --format "{{.Status}}" --filter "name=^$container$")
            print_success "Container: $container ($status)"
        else
            print_error "Container: $container (not running)"
            all_running=false
        fi
    done

    if [ "$all_running" = "true" ]; then
        return 0
    else
        return 1
    fi
}

# Main health check
main() {
    echo "Health Check for $ENVIRONMENT Environment"
    echo "========================================"
    echo ""

    # Check Docker containers first
    check_containers
    echo ""

    # Get URLs for the environment
    get_urls

    # Check DNS resolution for localhost domains
    if [ "$ENVIRONMENT" = "dev" ] || [ "$ENVIRONMENT" = "test" ]; then
        case "$ENVIRONMENT" in
            dev)
                domains=("api.docker.localhost" "app.docker.localhost" "chat.docker.localhost" "dashboard.docker.localhost")
                ;;
            test)
                domains=("api.test.localhost" "app.test.localhost" "chat.test.localhost" "dashboard.test.localhost")
                ;;
        esac

        for domain in "${domains[@]}"; do
            check_dns "$domain"
        done
        echo ""
    fi

    # Check service endpoints (pass host header for production)
    check_url "API Health" "$API_URL/health" "" "200" "$API_HOST"
    check_url "App Frontend" "$APP_URL/" "" "200" "$APP_HOST"
    check_url "Chat Service" "$CHAT_URL/" "" "200" "$CHAT_HOST"

    echo ""

    # Check WebSocket functionality for chat (skip for prod - requires more complex setup)
    if [ "$ENVIRONMENT" != "prod" ]; then
        check_websocket "Chat Service" "$CHAT_URL"
        echo ""
    fi

    # Check dashboard with authentication
    case "$ENVIRONMENT" in
        dev)
            check_url "Dashboard" "$DASHBOARD_URL/api/overview" "dev:devpass" "200"
            ;;
        test)
            check_url "Dashboard" "$DASHBOARD_URL/api/overview" "test:testpass" "200"
            ;;
        prod)
            print_info "Dashboard: Not exposed in production (security)"
            ;;
    esac

    echo ""
    print_info "Health check completed for $ENVIRONMENT environment"
}

# Show help
show_help() {
    echo "Health Check Script for Traefik Environments"
    echo ""
    echo "Usage: $0 [ENVIRONMENT]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  dev     - Development environment (default)"
    echo "  test    - Testing environment"
    echo "  prod    - Production environment"
    echo ""
    echo "This script checks:"
    echo "  • Docker container status"
    echo "  • DNS resolution (for dev/test)"
    echo "  • Service endpoints (API, App, Chat)"
    echo "  • WebSocket functionality"
    echo "  • Dashboard access (dev/test only)"
}

# Check for help
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main function
main
