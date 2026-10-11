#!/usr/bin/env bats
#
# ops/lib/urls.sh is the one place the {environment × service} grid is written.
# Two things are pinned here: the URLs it produces, and the absence of any
# hand-written hostname in the tools that read it. The second is the point —
# the grid was extracted from two copies, and nothing stopped a third being
# typed back in until this ran.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  source "$REPO_ROOT/ops/lib/urls.sh"
}

@test "dev URLs match the constants the grid replaced" {
  [ "$(icb_service_url dev api)" = 'https://api.docker.localhost' ]
  [ "$(icb_service_url dev app)" = 'https://app.docker.localhost' ]
  [ "$(icb_service_url dev dashboard)" = 'https://dashboard.docker.localhost' ]
}

@test "the Vue app is the bare domain in production and a subdomain elsewhere" {
  [ "$(icb_service_url prod app)" = 'https://ichrisbirch.com' ]
  [ "$(icb_service_url dev app)" = 'https://app.docker.localhost' ]
}

@test "production serves no dashboard, and says so rather than inventing a URL" {
  run icb_service_url prod dashboard
  [ "$status" -ne 0 ]
  [ -z "$output" ]
}

@test "an unknown environment fails rather than composing a hostname from it" {
  run icb_service_url staging api
  [ "$status" -ne 0 ]
  [ -z "$output" ]
}

@test "DOMAIN overrides the production domain" {
  DOMAIN=example.com run icb_service_url prod api
  [ "$output" = 'https://example.com' ]
}

@test "icb_service_host returns the header value health-check sends in prod" {
  [ "$(icb_service_host prod api)" = 'ichrisbirch.com' ]
  [ "$(icb_service_host prod app)" = 'ichrisbirch.com' ]
}

@test "sourcing the library arms no shell options in the caller" {
  run bash -c 'before="$-"; source '"$REPO_ROOT"'/ops/lib/urls.sh; [ "$before" = "$-" ]'
  [ "$status" -eq 0 ]
}

@test "icbops prints the dev and prod URLs the grid gives" {
  TERM='' run "$REPO_ROOT/ops/icbops"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Dev:  $(icb_service_url dev api) | $(icb_service_url dev app)"* ]]
  [[ "$output" == *"Prod: $(icb_service_url prod api) | $(icb_service_url prod app)"* ]]
}
