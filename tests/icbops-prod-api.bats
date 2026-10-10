#!/usr/bin/env bats
#
# prod apihealth and prod smoke reach production through the icb CLI's token.
# A stub icb and a stub curl first on PATH play the operator's machine, so
# nothing here leaves it.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  mkdir -p "$BATS_TEST_TMPDIR/bin"
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

stub() {
  local name=$1 body=$2
  printf '#!/usr/bin/env bash\n%s\n' "$body" >"$BATS_TEST_TMPDIR/bin/$name"
  chmod +x "$BATS_TEST_TMPDIR/bin/$name"
}

@test "prod apihealth exits non-zero when the operator's icb login has lapsed" {
  stub icb 'echo "Not logged in. Run icb auth login." >&2; exit 1'
  stub curl 'echo "curl must not run" >&2; exit 0'
  run "$REPO_ROOT/ops/icbops" prod apihealth
  [ "$status" -eq 1 ]
  [[ "$output" == *"Not logged in"* ]]
  [[ "$output" != *"curl must not run"* ]]
}

@test "prod apihealth exits non-zero and prints the body when the API answers with an error" {
  stub icb 'echo a-token'
  stub curl 'cat >/dev/null; echo "{\"detail\": \"database unavailable\"}"; exit 22'
  run "$REPO_ROOT/ops/icbops" prod apihealth
  [ "$status" -eq 1 ]
  [[ "$output" == *"database unavailable"* ]]
}
