#!/usr/bin/env bats
#
# The prod verbs that drive the host's containers run on the production host.
# Here they run in a scratch checkout whose install directory and blue/green
# state file are scratch paths, with a stub docker and a stub sops first on
# PATH, so nothing here reads or changes a real deployment. icbops runs under
# set -euo pipefail, and on these verbs an early exit leaves production half
# switched, so each is run to its end.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  CHECKOUT="$BATS_TEST_TMPDIR/checkout"
  SERVICES_FILE="$CHECKOUT/deploy-containers/traefik/dynamic/prod/services.yml"
  export STATE_FILE="$BATS_TEST_TMPDIR/bluegreen-state"
  export DOCKER_CALLS="$BATS_TEST_TMPDIR/docker-calls"
  : >"$DOCKER_CALLS"

  mkdir -p "$CHECKOUT/scripts" "$CHECKOUT/secrets" "$(dirname "$SERVICES_FILE")" \
    "$BATS_TEST_TMPDIR/install/logs" "$BATS_TEST_TMPDIR/bin"
  cp -R "$REPO_ROOT/ops" "$CHECKOUT/ops"
  cp "$REPO_ROOT/scripts/generate-services-yml.sh" "$CHECKOUT/scripts/"
  : >"$CHECKOUT/secrets/secrets.prod.enc.env"
  sed -e "s|^PROD_INSTALL_DIR=.*|PROD_INSTALL_DIR=\"$BATS_TEST_TMPDIR/install\"|" \
    -e "s|^BLUEGREEN_STATE_FILE=.*|BLUEGREEN_STATE_FILE=\"$STATE_FILE\"|" \
    "$REPO_ROOT/ops/icbops" >"$CHECKOUT/ops/icbops"
  grep -qx "PROD_INSTALL_DIR=\"$BATS_TEST_TMPDIR/install\"" "$CHECKOUT/ops/icbops"
  grep -qx "BLUEGREEN_STATE_FILE=\"$STATE_FILE\"" "$CHECKOUT/ops/icbops"

  echo blue >"$STATE_FILE"
  "$CHECKOUT/scripts/generate-services-yml.sh" blue "$SERVICES_FILE" setup

  cat >"$BATS_TEST_TMPDIR/bin/docker" <<'EOF'
#!/usr/bin/env bash
echo "$*" >>"$DOCKER_CALLS"
case "$*" in
  images*) echo "REPOSITORY   TAG" ;;
  *Health.Status*) echo healthy ;;
esac
exit 0
EOF
  printf '#!/usr/bin/env bash\necho SECRET_FROM_SOPS=value\n' >"$BATS_TEST_TMPDIR/bin/sops"
  chmod +x "$BATS_TEST_TMPDIR/bin/docker" "$BATS_TEST_TMPDIR/bin/sops"
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

@test "every prod verb that inspects or drives the host's containers runs to its end" {
  for verb in start stop restart status deploy-status "logs deploy" "logs build" build-test; do
    echo "verb: $verb"
    read -ra args <<<"$verb"
    run "$CHECKOUT/ops/icbops" prod "${args[@]}"
    [ "$status" -eq 0 ]
  done
  grep -q '^compose --project-name icb-blue -f docker-compose.app.yml up -d$' "$DOCKER_CALLS"
}

@test "rollback starts the standby color, then points routing and the state file at it" {
  run "$CHECKOUT/ops/icbops" prod rollback
  [ "$status" -eq 0 ]
  grep -q '^compose --project-name icb-green -f docker-compose.app.yml up -d$' "$DOCKER_CALLS"
  grep -q 'icb-green-api' "$SERVICES_FILE"
  [ "$(cat "$STATE_FILE")" = green ]
}

@test "rollback leaves the state file on the live color when routing cannot be rewritten" {
  printf '#!/usr/bin/env bash\nexit 1\n' >"$CHECKOUT/scripts/generate-services-yml.sh"
  run "$CHECKOUT/ops/icbops" prod rollback
  [ "$status" -ne 0 ]
  [ "$(cat "$STATE_FILE")" = blue ]
}
