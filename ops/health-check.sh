#!/usr/bin/env bash
# Health check script for Traefik environments
# Usage: ./health-check.sh [dev|test|prod]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The {environment × service} URL grid, shared with ops/icbops
source "${SCRIPT_DIR}/lib/urls.sh"

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
    dev | test)
      API_URL="$(icb_service_url "$ENVIRONMENT" api)"
      APP_URL="$(icb_service_url "$ENVIRONMENT" app)"
      DASHBOARD_URL="$(icb_service_url "$ENVIRONMENT" dashboard)"
      API_HOST=""
      APP_HOST=""
      ;;
    prod)
      # Production: hit Traefik locally with Host headers
      # Cloudflare Tunnel routes external traffic, but we can test via localhost
      API_URL="http://localhost:80"
      APP_URL="http://localhost:80"
      DASHBOARD_URL=""
      API_HOST="$(icb_service_host prod api)"
      APP_HOST="$(icb_service_host prod app)"
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

# Check DNS resolution
check_dns() {
  local domain="$1"

  print_info "Checking DNS resolution for $domain"

  if host "$domain" >/dev/null 2>&1; then
    local ip
    ip=$(host "$domain" | grep "has address" | awk '{print $4}' | head -1)
    if [ -n "$ip" ]; then
      print_success "DNS: $domain resolves to $ip"
      return 0
    fi
  fi

  # Check /etc/hosts
  if grep -q "$domain" /etc/hosts 2>/dev/null; then
    local ip
    ip=$(grep "$domain" /etc/hosts | awk '{print $1}' | head -1)
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
        "icb-dev-traefik"
        "icb-dev-api"
        "icb-dev-vue"
        "icb-dev-postgres"
        "icb-dev-redis"
        "icb-dev-scheduler"
      )
      ;;
    test)
      containers=(
        "icb-test-traefik"
        "icb-test-api"
        "icb-test-vue"
        "icb-test-postgres"
        "icb-test-redis"
        "icb-test-scheduler"
      )
      ;;
    prod)
      # Blue/green: check infra + active color containers
      local bluegreen_state="/var/lib/ichrisbirch/bluegreen-state"
      local active_color=""
      if [[ -f "$bluegreen_state" ]]; then
        active_color=$(cat "$bluegreen_state")
      fi

      if [[ -n "$active_color" ]]; then
        containers=(
          "icb-infra-traefik"
          "icb-infra-postgres"
          "icb-infra-redis"
          "icb-${active_color}-api"
          "icb-${active_color}-vue"
          "icb-${active_color}-scheduler"
        )
        print_info "Blue/green active color: $active_color"
      else
        # Legacy single-compose
        containers=(
          "icb-prod-traefik"
          "icb-prod-api"
          "icb-prod-vue"
          "icb-prod-postgres"
          "icb-prod-redis"
          "icb-prod-scheduler"
        )
      fi
      ;;
  esac

  local all_healthy=true

  for container in "${containers[@]}"; do
    # State.Status: running | restarting | exited | created | paused | dead
    local state
    state=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "missing")

    if [ "$state" = "missing" ]; then
      print_error "Container: $container (not found)"
      all_healthy=false
      continue
    fi

    # State.Health.Status: healthy | unhealthy | starting | <empty if no healthcheck>
    local health
    health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null || echo "none")

    local status
    status=$(docker ps -a --format "{{.Status}}" --filter "name=^$container$")

    case "$state" in
      running)
        case "$health" in
          healthy | none)
            print_success "Container: $container ($status)"
            ;;
          starting)
            print_warning "Container: $container ($status) — healthcheck starting"
            all_healthy=false
            ;;
          unhealthy)
            print_error "Container: $container ($status) — UNHEALTHY"
            all_healthy=false
            ;;
          *)
            print_warning "Container: $container ($status) — unknown health: $health"
            all_healthy=false
            ;;
        esac
        ;;
      restarting)
        print_error "Container: $container ($status) — RESTARTING (crash loop)"
        all_healthy=false
        ;;
      exited | dead)
        print_error "Container: $container ($status) — not running"
        all_healthy=false
        ;;
      *)
        print_warning "Container: $container ($status) — state: $state"
        all_healthy=false
        ;;
    esac
  done

  if [ "$all_healthy" = "true" ]; then
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

  # Check DNS resolution for localhost domains.
  # icb_env_domain rather than icb_env_suffix: check_dns runs `host`, which
  # takes a name and not a name:port.
  if [ "$ENVIRONMENT" = "dev" ] || [ "$ENVIRONMENT" = "test" ]; then
    local domain_suffix service
    domain_suffix=$(icb_env_domain "$ENVIRONMENT")

    while read -r service; do
      check_dns "${service}.${domain_suffix}"
    done < <(icb_services)
    echo ""
  fi

  # Check service endpoints (pass host header for production)
  check_url "API Health" "$API_URL/health" "" "200" "$API_HOST"
  check_url "App Frontend" "$APP_URL/" "" "200" "$APP_HOST"

  echo ""

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
  echo "  • Service endpoints (API, App)"
  echo "  • Dashboard access (dev/test only)"
}

# Check for help
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  show_help
  exit 0
fi

# Run main function
main
