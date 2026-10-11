#!/usr/bin/env bats
#
# Each checkout runs its own test stack, a compose project named after the
# checkout's directory. A stub docker first on PATH records every call and
# answers the few reads icbops makes: which checkout started this project's
# containers (STACK_CHECKOUT_FILE), which test projects exist with their
# checkouts (PROJECTS_FILE), and which per-project images exist (IMAGES_FILE).

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  PROJECT="icb-test-$(basename "$REPO_ROOT" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9_\n-' '-')"
  export DOCKER_CALLS="$BATS_TEST_TMPDIR/docker-calls"
  export STACK_CHECKOUT_FILE="$BATS_TEST_TMPDIR/stack-checkout"
  export PROJECTS_FILE="$BATS_TEST_TMPDIR/projects"
  export IMAGES_FILE="$BATS_TEST_TMPDIR/images"
  : >"$DOCKER_CALLS"
  : >"$PROJECTS_FILE"
  : >"$IMAGES_FILE"
  unset CI
  mkdir -p "$BATS_TEST_TMPDIR/bin"
  cat >"$BATS_TEST_TMPDIR/bin/docker" <<'EOF'
#!/usr/bin/env bash
echo "$*" >>"$DOCKER_CALLS"
last="${*: -1}"
case "$*" in
  "ps -a --filter label=com.docker.compose.project --format"*) cat "$PROJECTS_FILE" ;;
  "ps -a --filter label=com.docker.compose.project="*) [[ -s "$STACK_CHECKOUT_FILE" ]] && cat "$STACK_CHECKOUT_FILE" ;;
  "ps -aq --filter label=com.docker.compose.project="*) echo "container-of-${last##*=}" ;;
  "volume ls -q --filter label=com.docker.compose.project="*) echo "volume-of-${last##*=}" ;;
  "network ls -q --filter label=com.docker.compose.project="*) echo "network-of-${last##*=}" ;;
  "image ls ichrisbirch --format"*) cat "$IMAGES_FILE" ;;
  *Health.Status*) echo healthy ;;
esac
exit 0
EOF
  chmod +x "$BATS_TEST_TMPDIR/bin/docker"
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

@test "a checkout's stack is named after its directory, lowercased to what compose accepts" {
  mkdir -p "$BATS_TEST_TMPDIR/Feature.Branch"
  cp -R "$REPO_ROOT/ops" "$BATS_TEST_TMPDIR/Feature.Branch/ops"
  run "$BATS_TEST_TMPDIR/Feature.Branch/ops/icbops" testing restart
  [ "$status" -eq 0 ]
  grep -q '^compose --project-name icb-test-feature-branch .* up -d --wait' "$DOCKER_CALLS"
}

@test "testing stop takes down this checkout's stack and no other" {
  printf '%s %s\n' icb-test-other /elsewhere/other >"$PROJECTS_FILE"
  run "$REPO_ROOT/ops/icbops" testing stop
  [ "$status" -eq 0 ]
  grep -q "^compose --project-name ${PROJECT} .* down --volumes" "$DOCKER_CALLS"
  run grep -c 'other' "$DOCKER_CALLS"
  [ "$output" = 0 ]
}

@test "testing start removes every stack whose checkout is gone, its image included, and only those" {
  mkdir -p "$BATS_TEST_TMPDIR/alive/.git"
  printf '%s %s\n' \
    icb-test-landed "$BATS_TEST_TMPDIR/landed-worktree" \
    icb-test-alive "$BATS_TEST_TMPDIR/alive" \
    icb-dev "$BATS_TEST_TMPDIR/also-gone" >"$PROJECTS_FILE"
  run "$REPO_ROOT/ops/icbops" testing start
  [ "$status" -eq 0 ]
  grep -qx 'rm -f -v container-of-icb-test-landed' "$DOCKER_CALLS"
  grep -qx 'volume rm volume-of-icb-test-landed' "$DOCKER_CALLS"
  grep -qx 'network rm network-of-icb-test-landed' "$DOCKER_CALLS"
  grep -qx 'image rm ichrisbirch:icb-test-landed' "$DOCKER_CALLS"
  run grep -cE 'icb-test-alive|icb-dev' "$DOCKER_CALLS"
  [ "$output" = 0 ]
  grep -q "^compose --project-name ${PROJECT} .* up -d --wait" "$DOCKER_CALLS"
}

@test "a removed checkout whose container restarted holds only recreated mount directories, and testing start still removes its stack" {
  mkdir -p "$BATS_TEST_TMPDIR/restarted/.venv" "$BATS_TEST_TMPDIR/restarted/frontend/node_modules"
  echo '{}' >"$BATS_TEST_TMPDIR/restarted/frontend/package-lock.json"
  printf '%s %s\n' icb-test-restarted "$BATS_TEST_TMPDIR/restarted" >"$PROJECTS_FILE"
  run "$REPO_ROOT/ops/icbops" testing start
  [ "$status" -eq 0 ]
  grep -qx 'rm -f -v container-of-icb-test-restarted' "$DOCKER_CALLS"
  grep -qx 'image rm ichrisbirch:icb-test-restarted' "$DOCKER_CALLS"
}

@test "a checkout stopped before it was removed leaves only its image, which testing start removes while keeping every live checkout's" {
  printf '%s\n' "$PROJECT" icb-test-stopped-then-removed >"$IMAGES_FILE"
  run "$REPO_ROOT/ops/icbops" testing start
  [ "$status" -eq 0 ]
  grep -qx 'image rm ichrisbirch:icb-test-stopped-then-removed' "$DOCKER_CALLS"
  run grep -c "image rm ichrisbirch:${PROJECT}\$" "$DOCKER_CALLS"
  [ "$output" = 0 ]
}

@test "a rebuilt image's venv reaches the recreated containers, because every up renews their anonymous volumes" {
  for verb in "testing start" "testing restart" "testing rebuild" "testing rebuild --all" "testing rebuild --volumes"; do
    echo "verb: $verb"
    read -ra args <<<"$verb"
    : >"$DOCKER_CALLS"
    run "$REPO_ROOT/ops/icbops" "${args[@]}"
    [ "$status" -eq 0 ]
    grep -q ' up ' "$DOCKER_CALLS"
    run bash -c "grep ' up ' '$DOCKER_CALLS' | grep -vc -- '--renew-anon-volumes'"
    [ "$output" = 0 ]
  done
}

@test "test e2e runs Playwright in this stack's vue container as the caller" {
  run "$REPO_ROOT/ops/icbops" test e2e e2e/tasks.spec.ts --trace on
  [ "$status" -eq 0 ]
  grep -q "^compose --project-name ${PROJECT} .* exec --user $(id -u):$(id -g) --env HOME=/tmp -T vue npx playwright test e2e/tasks.spec.ts --trace on\$" "$DOCKER_CALLS"
}

@test "under CI the stack takes the CI compose file and Playwright sees CI" {
  CI=true run "$REPO_ROOT/ops/icbops" test e2e
  [ "$status" -eq 0 ]
  grep -q "^compose --project-name ${PROJECT} .* -f docker-compose.ci.yml exec .* --env CI=true vue npx playwright test\$" "$DOCKER_CALLS"
}

@test "every verb that brings the stack up or writes its database refuses a same-named clone's stack" {
  echo /elsewhere/ichrisbirch >"$STACK_CHECKOUT_FILE"
  for verb in "test e2e" "testing start" "testing restart" "testing rebuild" "testing ensure" "testing db seed"; do
    echo "verb: $verb"
    read -ra args <<<"$verb"
    : >"$DOCKER_CALLS"
    run "$REPO_ROOT/ops/icbops" "${args[@]}"
    [ "$status" -eq 1 ]
    [[ "$output" == *"started from /elsewhere/ichrisbirch"* ]]
    run grep -c '^compose \|^exec ' "$DOCKER_CALLS"
    [ "$output" = 0 ]
  done
}

@test "testing stop takes down a stack a same-named clone started, which is how it is taken over" {
  echo /elsewhere/ichrisbirch >"$STACK_CHECKOUT_FILE"
  run "$REPO_ROOT/ops/icbops" testing stop
  [ "$status" -eq 0 ]
  grep -q "^compose --project-name ${PROJECT} .* down --volumes" "$DOCKER_CALLS"
}
