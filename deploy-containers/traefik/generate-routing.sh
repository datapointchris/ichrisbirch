#!/usr/bin/env bash
# Regenerate Traefik vue-paths rules from vue-paths.txt
#
# Reads the canonical path list and stamps it into the PathPrefix rule line
# in each environment's routing.yml. Everything else in the routing files
# (routers, middlewares, TLS, extra routes) is hand-authored.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATHS_FILE="$SCRIPT_DIR/vue-paths.txt"
DYNAMIC_DIR="$SCRIPT_DIR/dynamic"

# Traefik uses backticks in rules; store as variable to avoid shell interpretation
BT='`'

# Read paths, skip comments and blank lines
mapfile -t PATHS < <(grep -v '^#' "$PATHS_FILE" | grep -v '^$')

if [[ ${#PATHS[@]} -eq 0 ]]; then
    echo "ERROR: No paths found in $PATHS_FILE" >&2
    exit 1
fi

# Build "PathPrefix(`/x`) || PathPrefix(`/y`) || ..." from an array
build_prefixes() {
    local parts=""
    for path in "$@"; do
        [[ -n "$parts" ]] && parts="$parts || "
        parts="${parts}PathPrefix(${BT}${path}${BT})"
    done
    echo "$parts"
}

APP_PREFIXES=$(build_prefixes "${PATHS[@]}")

# Vite dev server paths (dev/test only — HMR, source maps, module resolution)
VITE_PATHS=("/@vite" "/@fs" "/@id" "/node_modules" "/src" "/__vite")
VITE_PREFIXES=$(build_prefixes "${VITE_PATHS[@]}")

# Dev/test rule: app paths + root + Vite paths
DEVTEST_RULE="${APP_PREFIXES} || Path(${BT}/${BT}) || ${VITE_PREFIXES}"

# Prod rule: app paths + /assets (built by Vite, served by Caddy) + root
PROD_RULE="${APP_PREFIXES} || PathPrefix(${BT}/assets${BT}) || Path(${BT}/${BT})"

# Replace a single line in a file using awk (avoids sed backtick escaping)
replace_line() {
    local file="$1" line_num="$2" new_content="$3"
    awk -v ln="$line_num" -v new="$new_content" 'NR==ln{print new;next}1' "$file" > "${file}.tmp"
    mv "${file}.tmp" "$file"
}

# Find the vue-paths rule line and replace it
update_rule() {
    local file="$1" line_num="$2" host="$3" rule="$4"
    local full_line="      rule: \"Host(${BT}${host}${BT}) && (${rule})\""
    replace_line "$file" "$line_num" "$full_line"
    echo "  $(basename "$(dirname "$file")")/$(basename "$file"):${line_num}"
}

echo "Generating vue-paths rules from $(basename "$PATHS_FILE") (${#PATHS[@]} paths)..."

# Dev: app.docker.localhost
LN=$(grep -n 'app\.docker\.localhost.*PathPrefix' "$DYNAMIC_DIR/dev/routing.yml" | head -1 | cut -d: -f1)
[[ -z "$LN" ]] && { echo "ERROR: vue-paths rule not found in dev/routing.yml" >&2; exit 1; }
update_rule "$DYNAMIC_DIR/dev/routing.yml" "$LN" "app.docker.localhost" "$DEVTEST_RULE"

# Test: app.test.localhost
LN=$(grep -n 'app\.test\.localhost.*PathPrefix' "$DYNAMIC_DIR/test/routing.yml" | head -1 | cut -d: -f1)
[[ -z "$LN" ]] && { echo "ERROR: vue-paths rule not found in test/routing.yml" >&2; exit 1; }
update_rule "$DYNAMIC_DIR/test/routing.yml" "$LN" "app.test.localhost" "$DEVTEST_RULE"

# Prod: ichrisbirch.com (non-www — match countdowns to skip the api-proxy rule)
LN=$(grep -n 'ichrisbirch\.com.*countdowns' "$DYNAMIC_DIR/prod/routing.yml" | grep -v 'www\.' | head -1 | cut -d: -f1)
[[ -z "$LN" ]] && { echo "ERROR: vue-paths rule not found in prod/routing.yml" >&2; exit 1; }
update_rule "$DYNAMIC_DIR/prod/routing.yml" "$LN" "ichrisbirch.com" "$PROD_RULE"

# Prod: www.ichrisbirch.com
LN=$(grep -n 'www\.ichrisbirch\.com.*PathPrefix' "$DYNAMIC_DIR/prod/routing.yml" | head -1 | cut -d: -f1)
[[ -z "$LN" ]] && { echo "ERROR: www vue-paths rule not found in prod/routing.yml" >&2; exit 1; }
update_rule "$DYNAMIC_DIR/prod/routing.yml" "$LN" "www.ichrisbirch.com" "$PROD_RULE"

echo "Done."
