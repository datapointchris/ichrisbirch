#!/usr/bin/env bats
#
# Compose names what it builds after the service's image:. So an override that
# swaps a built service to a public image without resetting build: builds this
# Dockerfile and tags the result as that public image. The vue service once
# overwrote the local node:20-alpine that way four times before anyone noticed.
# Every compose set this repo runs is resolved through compose's own loader,
# which applies anchors, !reset, !override and the order the files stack in.

# Each set as its runner passes it: icbops for prod, dev, test and infra,
# validate.yml for ci, and the blue/green deploy for app.
COMPOSE_SETS=(
  "docker-compose.yml"
  "docker-compose.yml docker-compose.dev.yml"
  "docker-compose.yml docker-compose.test.yml"
  "docker-compose.yml docker-compose.test.yml docker-compose.ci.yml"
  "docker-compose.infra.yml"
  "docker-compose.app.yml"
)

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
  cd "$REPO_ROOT" || return 1
}

# Prints each service that builds under an image name this project does not own.
foreign_builds() {
  local args=() file resolved
  for file in "$@"; do args+=(-f "$file"); done
  resolved=$(DEPLOY_COLOR=blue docker compose --project-name icb-build-tags "${args[@]}" \
    config --format json 2>"$BATS_TEST_TMPDIR/compose.err") || {
    cat "$BATS_TEST_TMPDIR/compose.err"
    return 1
  }
  jq -r '.services | to_entries[]
    | select(.value.build != null and .value.image != null)
    | select(.value.image | test("^ichrisbirch(-[a-z]+)?:") | not)
    | "\(.key) builds as \(.value.image)"' <<<"$resolved"
}

@test "every compose set tags what it builds under this project's name" {
  for set in "${COMPOSE_SETS[@]}"; do
    echo "set: $set"
    read -ra files <<<"$set"
    run foreign_builds "${files[@]}"
    echo "$output"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
  done
}

@test "every compose file in the repo belongs to a checked set" {
  for file in docker-compose*.yml; do
    [[ " ${COMPOSE_SETS[*]} " == *" $file "* ]] || {
      echo "$file is in no set"
      return 1
    }
  done
}

@test "an override naming a public image on a built service is reported, and one resetting build is not" {
  cd "$BATS_TEST_TMPDIR" || return 1
  cat >base.yml <<'EOF'
services:
  vue:
    build: .
    image: ichrisbirch-vue:production
EOF
  cat >swaps-image.yml <<'EOF'
services:
  vue:
    image: node:24-alpine
EOF
  cat >resets-build.yml <<'EOF'
services:
  vue:
    image: node:24-alpine
    build: !reset null
EOF

  run foreign_builds base.yml swaps-image.yml
  [ "$status" -eq 0 ]
  [ "$output" = "vue builds as node:24-alpine" ]

  run foreign_builds base.yml resets-build.yml
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
