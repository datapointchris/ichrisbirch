#!/usr/bin/env bats
#
# The test stack's vue container runs Playwright's image, and the e2e suite runs
# inside it with the @playwright/test that package-lock.json installs. That
# package launches only the browser build its own version names, so an image
# from another release fails every spec with the browser missing.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd -P)"
}

@test "the vue test image's Playwright release is the one package-lock.json installs" {
  locked=$(jq -r '.packages["node_modules/@playwright/test"].version' "$REPO_ROOT/frontend/package-lock.json")
  image=$(yq -r '.services.vue.image' "$REPO_ROOT/docker-compose.test.yml")
  echo "locked: $locked, image: $image"
  [ "$image" = "mcr.microsoft.com/playwright:v${locked}-noble" ]
}
