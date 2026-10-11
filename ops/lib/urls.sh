#!/usr/bin/env bash
# shellcheck shell=bash
#
# The {environment × service} URL grid, sourced by ops/icbops and
# ops/health-check.sh. Both need the same hostnames, so both derive them here.
# The test stack has no row: it publishes no ports, so no host tool reaches it.
#
# No `set` options: this is sourced into the caller's shell and the caller owns
# its own error strategy.

# The domain an environment's services answer on.
# Globals:
#   DOMAIN - production only; defaults to ichrisbirch.com when unset
# Arguments:
#   $1 - environment: dev or prod
# Outputs:
#   The domain, on stdout
# Returns:
#   1 for an unknown environment, having written nothing
icb_env_domain() {
  case "$1" in
    dev) echo 'docker.localhost' ;;
    prod) echo "${DOMAIN:-ichrisbirch.com}" ;;
    *) return 1 ;;
  esac
}

# The hostname a service answers on in one environment. Production breaks the
# subdomain pattern: the Vue app is the bare domain, the API shares it under
# the path icb_service_path gives, and there is no Traefik dashboard.
# Arguments:
#   $1 - environment: dev or prod
#   $2 - service: api, app, dashboard
# Outputs:
#   The hostname, on stdout
# Returns:
#   1 for an unknown environment or for prod:dashboard, having written nothing
icb_service_host() {
  local environment="$1" service="$2" domain
  domain=$(icb_env_domain "$environment") || return 1
  case "${environment}:${service}" in
    prod:app | prod:api) echo "$domain" ;;
    prod:dashboard) return 1 ;;
    *) echo "${service}.${domain}" ;;
  esac
}

# The path a service is mounted under on its host, empty where it owns the
# host. Production's API sits behind the same-origin proxy that strips /api.
# Arguments:
#   $1 - environment: dev or prod
#   $2 - service: api, app, dashboard
# Outputs:
#   The path with its leading slash, or nothing, on stdout
icb_service_path() {
  case "$1:$2" in
    prod:api) echo '/api' ;;
  esac
}

# The URL a browser would use. Traefik terminates TLS in every environment.
# Arguments:
#   $1 - environment: dev or prod
#   $2 - service: api, app, dashboard
# Outputs:
#   The https URL, on stdout
# Returns:
#   1 wherever icb_service_host does, having written nothing
icb_service_url() {
  local host
  host=$(icb_service_host "$1" "$2") || return 1
  echo "https://${host}$(icb_service_path "$1" "$2")"
}

# Every service reachable through Traefik, for a caller that iterates rather
# than naming one. A function and not a string, because an unquoted expansion
# does not word-split under zsh and this file has no control over the shell it
# is sourced into.
# Outputs:
#   One service name per line, on stdout
icb_services() {
  printf '%s\n' api app dashboard
}
