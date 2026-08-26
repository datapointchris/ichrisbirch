#!/usr/bin/env bash
# shellcheck shell=bash
#
# The {environment × service} URL grid, sourced by ops/icbops and
# ops/health-check.sh. Both need the same hostnames, so both derive them here.
#
# No `set` options: this is sourced into the caller's shell and the caller owns
# its own error strategy.

# The host suffix an environment's services answer on. Test carries a port
# because its Traefik listener is not on 443; dev and prod answer on the default.
icb_env_suffix() {
  case "$1" in
    dev) echo 'docker.localhost' ;;
    test) echo 'test.localhost:8443' ;;
    prod) echo "${DOMAIN:-ichrisbirch.com}" ;;
    *) return 1 ;;
  esac
}

# The hostname a service answers on in one environment. Two services break the
# subdomain pattern: the Vue app is the bare domain in production, and
# production serves no Traefik dashboard. Both return non-zero rather than a
# wrong URL.
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
icb_service_url() {
  local host
  host=$(icb_service_host "$1" "$2") || return 1
  echo "https://${host}"
}
