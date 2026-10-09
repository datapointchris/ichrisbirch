#!/usr/bin/env bats
#
# The test stack is one compose project shared by every checkout of this repo.
# A stub docker first on PATH plays a stack started from the checkout written
# to STACK_CHECKOUT_FILE and records every call, so a refused verb can be shown
# to reach no compose call.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  export DOCKER_CALLS="$BATS_TEST_TMPDIR/docker-calls"
  export STACK_CHECKOUT_FILE="$BATS_TEST_TMPDIR/stack-checkout"
  : >"$DOCKER_CALLS"
  mkdir -p "$BATS_TEST_TMPDIR/bin"
  cat >"$BATS_TEST_TMPDIR/bin/docker" <<'EOF'
#!/usr/bin/env bash
echo "$*" >>"$DOCKER_CALLS"
case "$*" in
  ps\ *project.working_dir*) [[ -s "$STACK_CHECKOUT_FILE" ]] && cat "$STACK_CHECKOUT_FILE" ;;
  *Health.Status*) echo healthy ;;
esac
exit 0
EOF
  chmod +x "$BATS_TEST_TMPDIR/bin/docker"
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

@test "every verb that brings the stack up or writes its database refuses another checkout's stack" {
  echo /elsewhere/ichrisbirch >"$STACK_CHECKOUT_FILE"
  for verb in "test run" "testing start" "testing restart" "testing rebuild" "testing ensure" "testing db seed"; do
    echo "verb: $verb"
    read -ra args <<<"$verb"
    : >"$DOCKER_CALLS"
    run "$REPO_ROOT/ops/icbops" "${args[@]}"
    [ "$status" -eq 1 ]
    [[ "$output" == *"started from /elsewhere/ichrisbirch"* ]]
    run grep -c '^compose ' "$DOCKER_CALLS"
    [ "$output" = 0 ]
  done
}

@test "the checkout that started the stack restarts it" {
  echo "$REPO_ROOT" >"$STACK_CHECKOUT_FILE"
  run "$REPO_ROOT/ops/icbops" testing restart
  [ "$status" -eq 0 ]
  grep -q '^compose --project-name icb-test .* up -d' "$DOCKER_CALLS"
}

@test "with no test containers at all, any checkout starts the stack" {
  run "$REPO_ROOT/ops/icbops" testing restart
  [ "$status" -eq 0 ]
  grep -q '^compose --project-name icb-test .* up -d' "$DOCKER_CALLS"
}

@test "testing stop takes down a stack another checkout started, which is how it is taken over" {
  echo /elsewhere/ichrisbirch >"$STACK_CHECKOUT_FILE"
  run "$REPO_ROOT/ops/icbops" testing stop
  [ "$status" -eq 0 ]
  grep -q '^compose --project-name icb-test .* down --volumes' "$DOCKER_CALLS"
}
