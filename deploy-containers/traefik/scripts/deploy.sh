#!/usr/bin/env bash
# Deploy script for Traefik-based environments
# Usage: ./deploy.sh [dev|test|prod] [up|down|restart|logs|status]

set -e

# Default values
ENVIRONMENT="${1:-dev}"
ACTION="${2:-up}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Validate environment
validate_environment() {
    case "$ENVIRONMENT" in
        dev|test|prod)
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            print_info "Valid environments: dev, test, prod"
            exit 1
            ;;
    esac
}

# Check if proxy network exists
ensure_proxy_network() {
    if ! docker network inspect proxy >/dev/null 2>&1; then
        print_info "Creating external proxy network..."
        docker network create proxy
        print_success "Proxy network created"
    else
        print_info "Proxy network already exists"
    fi
}

# Get compose file for environment
get_compose_file() {
    case "$ENVIRONMENT" in
        dev)
            echo "docker-compose.dev.yml"
            ;;
        test)
            echo "docker-compose.test.yml"
            ;;
        prod)
            echo "docker-compose.yml"
            ;;
    esac
}

# Deploy environment
deploy_up() {
    local compose_file=$(get_compose_file)

    print_info "Deploying $ENVIRONMENT environment using $compose_file"

    # Ensure proxy network exists
    ensure_proxy_network

    # Change to project root
    cd "$PROJECT_ROOT"

    # Deploy with appropriate compose file
    if [ "$ENVIRONMENT" = "prod" ]; then
        docker-compose up -d
    else
        docker-compose -f "$compose_file" up -d
    fi

    print_success "$ENVIRONMENT environment deployed successfully"

    # Show service status
    show_status
}

# Stop environment
deploy_down() {
    local compose_file=$(get_compose_file)

    print_info "Stopping $ENVIRONMENT environment"

    cd "$PROJECT_ROOT"

    if [ "$ENVIRONMENT" = "prod" ]; then
        docker-compose down
    else
        docker-compose -f "$compose_file" down
    fi

    print_success "$ENVIRONMENT environment stopped"
}

# Restart environment
deploy_restart() {
    print_info "Restarting $ENVIRONMENT environment"
    deploy_down
    sleep 2
    deploy_up
}

# Show logs
show_logs() {
    local compose_file=$(get_compose_file)
    local service="${3:-}"

    cd "$PROJECT_ROOT"

    if [ -n "$service" ]; then
        print_info "Showing logs for $service in $ENVIRONMENT environment"
        if [ "$ENVIRONMENT" = "prod" ]; then
            docker-compose logs -f "$service"
        else
            docker-compose -f "$compose_file" logs -f "$service"
        fi
    else
        print_info "Showing logs for $ENVIRONMENT environment"
        if [ "$ENVIRONMENT" = "prod" ]; then
            docker-compose logs -f
        else
            docker-compose -f "$compose_file" logs -f
        fi
    fi
}

# Show status
show_status() {
    print_info "Environment: $ENVIRONMENT"
    print_info "Services status:"

    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=ichrisbirch"
    echo ""

    # Show environment-specific URLs
    case "$ENVIRONMENT" in
        dev)
            print_info "Development URLs:"
            echo "  • API:       https://api.docker.localhost/"
            echo "  • App:       https://app.docker.localhost/"
            echo "  • Chat:      https://chat.docker.localhost/"
            echo "  • Dashboard: https://dashboard.docker.localhost/ (user: dev, pass: devpass)"
            ;;
        test)
            print_info "Test URLs:"
            echo "  • API:       https://api.test.localhost:8443/"
            echo "  • App:       https://app.test.localhost:8443/"
            echo "  • Chat:      https://chat.test.localhost:8443/"
            echo "  • Dashboard: https://dashboard.test.localhost:8443/ (user: test, pass: testpass)"
            ;;
        prod)
            print_info "Production URLs (replace yourdomain.local with your actual domain):"
            echo "  • API:       https://api.yourdomain.local/"
            echo "  • App:       https://app.yourdomain.local/"
            echo "  • Chat:      https://chat.yourdomain.local/"
            ;;
    esac
}

# Show help
show_help() {
    echo "Traefik Deployment Script for iChrisBirch"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [ACTION] [SERVICE]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  dev     - Development environment (default)"
    echo "  test    - Testing environment"
    echo "  prod    - Production environment"
    echo ""
    echo "ACTION:"
    echo "  up      - Deploy environment (default)"
    echo "  down    - Stop environment"
    echo "  restart - Restart environment"
    echo "  logs    - Show logs (optionally for specific service)"
    echo "  status  - Show service status and URLs"
    echo "  help    - Show this help message"
    echo ""
    echo "SERVICE (optional, for logs action):"
    echo "  traefik - Traefik reverse proxy"
    echo "  api     - FastAPI backend"
    echo "  app     - Flask frontend"
    echo "  chat    - Streamlit chat service"
    echo "  postgres - PostgreSQL database"
    echo "  redis   - Redis cache"
    echo "  scheduler - Background scheduler"
    echo ""
    echo "Examples:"
    echo "  $0 dev up           # Deploy development environment"
    echo "  $0 test down        # Stop test environment"
    echo "  $0 prod restart     # Restart production environment"
    echo "  $0 dev logs api     # Show API logs in dev environment"
    echo "  $0 test status      # Show test environment status"
}

# Main execution
main() {
    validate_environment

    case "$ACTION" in
        up)
            deploy_up
            ;;
        down)
            deploy_down
            ;;
        restart)
            deploy_restart
            ;;
        logs)
            show_logs "$@"
            ;;
        status)
            show_status
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Invalid action: $ACTION"
            print_info "Valid actions: up, down, restart, logs, status, help"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
