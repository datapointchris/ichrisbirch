#!/usr/bin/env bash
# shellcheck shell=bash
#
# The {environment × service} URL grid, sourced by ops/icbops and
# ops/health-check.sh. Both need the same hostnames, so both derive them here.
#
# No `set` options: this is sourced into the caller's shell and the caller owns
# its own error strategy.

# The domain an environment's services answer on, without a port.
# Globals:
#   DOMAIN - production only; defaults to ichrisbirch.com when unset
# Arguments:
#   $1 - environment: dev, test or prod
# Outputs:
#   The domain, on stdout
# Returns:
#   1 for an unknown environment, having written nothing
icb_env_domain() {
  case "$1" in
    dev) echo 'docker.localhost' ;;
    test) echo 'test.localhost' ;;
    prod) echo "${DOMAIN:-ichrisbirch.com}" ;;
    *) return 1 ;;
  esac
}

# The host suffix an environment's services answer on, carrying the port where
# Traefik does not listen on 443. Anything resolving a name rather than opening
# a connection wants icb_env_domain instead, because `host` and DNS take no port.
# Arguments:
#   $1 - environment: dev, test or prod
# Outputs:
#   The suffix, on stdout
# Returns:
#   1 for an unknown environment, having written nothing
icb_env_suffix() {
  local domain
  domain=$(icb_env_domain "$1") || return 1
  case "$1" in
    test) echo "${domain}:8443" ;;
    *) echo "$domain" ;;
  esac
}

# The hostname a service answers on in one environment. Two cases break the
# subdomain pattern: the Vue app is the bare domain in production, and
# production serves no Traefik dashboard.
# Arguments:
#   $1 - environment: dev, test or prod
#   $2 - service: api, app, dashboard
# Outputs:
#   The hostname, on stdout
# Returns:
#   1 for an unknown environment or for prod:dashboard, having written nothing
icb_service_host() {
  local environment="$1" service="$2" suffix
  suffix=$(icb_env_suffix "$environment") || return 1
  case "${environment}:${service}" in
    prod:app) echo "$suffix" ;;
    prod:dashboard) return 1 ;;
    *) echo "${service}.${suffix}" ;;
  esac
}

# The URL a browser would use. Traefik terminates TLS in every environment.
# Arguments:
#   $1 - environment: dev, test or prod
#   $2 - service: api, app, dashboard
# Outputs:
#   The https URL, on stdout
# Returns:
#   1 wherever icb_service_host does, having written nothing
icb_service_url() {
  local host
  host=$(icb_service_host "$1" "$2") || return 1
  echo "https://${host}"
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
