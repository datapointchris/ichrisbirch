#!/usr/bin/env bats
#
# A help flag after a verb prints the verb's group usage and acts on nothing.
# `install --help` once installed, and `prod rollback --help` on the host would
# have switched production's traffic. A stub docker first on PATH records any
# call, and HOME is a scratch directory, so nothing here touches the machine.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  mkdir -p "$BATS_TEST_TMPDIR/bin" "$BATS_TEST_TMPDIR/home"
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
  export HOME="$BATS_TEST_TMPDIR/home"
  printf '#!/usr/bin/env bash\necho "$*" >>"%s/docker-calls"\n' "$BATS_TEST_TMPDIR" >"$BATS_TEST_TMPDIR/bin/docker"
  chmod +x "$BATS_TEST_TMPDIR/bin/docker"
}

@test "install --help prints the usage and installs nothing" {
  run "$REPO_ROOT/ops/icbops" install --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"icbops"* ]]
  [ ! -e "$HOME/.local/bin/icbops" ]
}

@test "a verb given --help prints its group's usage and runs no docker" {
  run "$REPO_ROOT/ops/icbops" dev stop --help
  [[ "$status" -eq 0 && "$output" == *"Dev commands"* ]]
  run "$REPO_ROOT/ops/icbops" testing start --help
  [[ "$status" -eq 0 && "$output" == *"Testing commands"* ]]
  run "$REPO_ROOT/ops/icbops" testing stop -h
  [[ "$status" -eq 0 && "$output" == *"Testing commands"* ]]
  run "$REPO_ROOT/ops/icbops" prod rollback --help
  [[ "$status" -eq 0 && "$output" == *"Prod commands"* ]]
  run "$REPO_ROOT/ops/icbops" test run --help
  [[ "$status" -eq 0 && "$output" == *"Test commands"* ]]
  [ ! -e "$BATS_TEST_TMPDIR/docker-calls" ]
}
